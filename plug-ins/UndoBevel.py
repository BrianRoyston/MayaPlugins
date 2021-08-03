import sys
import math
import os
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from maya import cmds

# Brian Royston
# 2021



kPluginCmdName = "undoBevel"



# Command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
        
    # Invoked when the command is run.
    def doIt(self,argList):
        undoBevel()
        
def splitName(name):
    """Given Face, Edge, Vertex, etc in the [#:#] form, splits them, otherwise does nothing"""
    split = name.split('[')
    objectName = split[0]
    numbersFull = split[1]
    result = []
    numbers = numbersFull.split(':')
    if len(numbers) == 1:
        result.append(objectName + "[" + numbersFull)
    elif len(numbers) == 2:
        number1 = int(numbers[0].replace(']', ''))
        number2 = int(numbers[1].replace(']', ''))
        for number in range(number1, number2 + 1):
            result.append(objectName + "[" + str(number) + "]")
    else:
        cmds.error("Should not be possible")
    return result

def splitNames(names):
    """Given a list of Faces, Edges, Vertices, etc, splits apart any that are in the [#:#]
        Note: there should be a built in command or flag to solve this... i couldnt find it """
    result = []
    for name in names:
        split = splitName(name)
        for newName in split:
            result.append(newName)
    return result

def printMVector(vector):
    print("[" + str(vector.x) + ", " + str(vector.y) + ", " + str(vector.z) + "]")

def scalarMVectorMul(scalar, vector):
    return OpenMaya.MVector(scalar * vector.x, scalar * vector.y, scalar * vector.z)

def distance(x1, y1, z1, x2, y2, z2):
    """Returns the distance between two points"""
    return math.sqrt(math.pow(x1 - x2, 2.0) + math.pow(y1 - y2, 2.0) + math.pow(z1 - z2, 2.0))

def closestVertex(edge, point):
    """Given an edge and an MVector or MPoint, returns the vertex of the edge closest to that point"""
    vertices = splitNames(cmds.polyListComponentConversion(edge, fromEdge = True, toVertex = True))

    vertex1, vertex2 = vertices[0], vertices[1]
    x1, y1, z1 = [cmds.pointPosition(vertex1)[i] for i in (0,1,2)]
    x2, y2, z2= [cmds.pointPosition(vertex2)[i] for i in (0,1,2)]
    d1 = abs(distance(x1, y1, z1, point.x, point.y, point.z))
    d2 = abs(distance(x2, y2, z2, point.x, point.y, point.z))

    if d1 < d2:
        return vertex1
    else:
        return vertex2

def edgeLength(edge):
    """Returns the length of a given edge"""
    vertices = splitNames(cmds.polyListComponentConversion(edge, fromEdge = True, toVertex = True))

    vertex1, vertex2 = vertices[0], vertices[1]
    x1, y1, z1 = [cmds.pointPosition(vertex1)[i] for i in (0,1,2)]
    x2, y2, z2= [cmds.pointPosition(vertex2)[i] for i in (0,1,2)]
    return distance(x1, y1, z1, x2, y2, z2)

def inRange(a, b, c, d, rangeVal):
    """Returns whether or not a, b, c, and d are all within an accepted range"""
    return (max(a, b, c, d) - min(a, b, c, d)) <= rangeVal

def calculateColisionPlanes(plane1, plane2, plane3):
    n1 = plane1.normal()
    n2 = plane2.normal()
    n3 = plane3.normal()
    d1 = plane1.distance()
    d2 = plane2.distance()
    d3 = plane3.distance()
    n_mat = OpenMaya.MMatrix()

    util = OpenMaya.MScriptUtil()

    #matList = [n1.x, n1.y, n1.z, 0.0, n2.x, n2.y, n2.z, 0.0, n3.x, n3.y, n3.z, 0.0, 0.0,  0.0,  0.0,  0.0]
    matList = [n1.x, n2.x, n3.x, 0.0, n1.y, n2.y, n3.y, 0.0, n1.z, n2.z, n3.z, 0.0, 0.0,  0.0,  0.0,  0.0]

    util.createMatrixFromList(matList, n_mat)

    n_mat = n_mat.inverse()
    d_vec = OpenMaya.MPoint(d1, d2, d3)

    return d_vec * n_mat  


def calculateColision(edge, face):
    """Given a face and an edge, calculates the point of intersection if the face, and edge are extended into a plane and a line"""
    b, p = getLineFromEdge(edge)
    plane = getPlaneFromFace(face)
    n, d = plane.normal(), plane.distance()

    if abs(n * p) == 0.0:
        return None 

    t = (d - n * b) / (n * p)

    return b + scalarMVectorMul(t, p)

def getLineFromEdge(edge):
    """Given an edge, returns the line extending that edge in vector form r_vec = b_vec + t * p_vec"""
    vertices = splitNames(cmds.polyListComponentConversion(edge, fromEdge = True, toVertex = True))
    vertex1, vertex2 = vertices[0], vertices[1]
    x1, y1, z1 = [cmds.pointPosition(vertex1)[i] for i in (0,1,2)]
    x2, y2, z2= [cmds.pointPosition(vertex2)[i] for i in (0,1,2)]
    a = OpenMaya.MVector(x1, y1, z1)
    b = OpenMaya.MVector(x2, y2, z2) 
    p = b - a
    return b, p

def getPlaneFromFace(face):
    """Given a face, returns the plane extending that face in vector form n_vec * r_vec = D"""
    vertices = splitNames(cmds.polyListComponentConversion(face, fromFace = True, toVertex = True))

    vertex1, vertex2, vertex3 = vertices[0], vertices[1], vertices[2]
    if len(vertices) > 3:
        vertices = vertices[3:]
    else:
        vertices = []
    x1, y1, z1 = [cmds.pointPosition(vertex1)[i] for i in (0,1,2)]
    x2, y2, z2= [cmds.pointPosition(vertex2)[i] for i in (0,1,2)]
    x3, y3, z3= [cmds.pointPosition(vertex3)[i] for i in (0,1,2)]
    plane = OpenMaya.MPlane()
    a = OpenMaya.MVector(x1, y1, z1)
    b = OpenMaya.MVector(x2, y2, z2)
    c = OpenMaya.MVector(x3, y3, z3)
    p1 = b - a 
    p2 = c - a 
    n = p1 ^ p2
    d = n * c
    plane.setPlane(n, d) 

    for vertex in vertices:
        x, y, z = [cmds.pointPosition(vertex)[i] for i in (0,1,2)]
        p = OpenMaya.MVector(x, y, z)
        #if abs(p * n) < 0.05:
             #cmds.error("Non Planar")
    return plane


def edgesTouching(edge1, edge2):
    """Returns whether the 2 edges share exactly 1 edge"""
    edge1Points = splitNames(cmds.polyListComponentConversion(edge1, fromEdge = True, toVertex = True))
    edge2Points = splitNames(cmds.polyListComponentConversion(edge2, fromEdge = True, toVertex = True))

    return edge1 != edge2 and ((edge1Points[0] in edge2Points) or (edge1Points[1] in edge2Points))


def matchEdge(edge1, face1, edge2, face2, movedVertices):
    """Moves edge1 on face1 to the projected position on face2, and deletes edge2"""
    face1Edges = splitNames(cmds.polyListComponentConversion(face1, fromFace = True, toEdge = True))
    sideEdge1 = ""
    sideEdge2 = ""
    
    for edge in face1Edges:
        if edgesTouching(edge, edge1):
            if sideEdge1 == "":
                sideEdge1 = edge
            elif sideEdge2 == "":
                sideEdge2 = edge
            else:
                cmds.error("Invalid Bevel")

    if sideEdge2 == "":
        cmds.error("Invalid Bevel")

    
    newVert1 = calculateColision(sideEdge1, face2)
    newVert2 = calculateColision(sideEdge2, face2) 

    if newVert1 is None or newVert2 is None:
        return False
        
    movingVert1 = closestVertex(sideEdge1, newVert1)
    movingVert2 = closestVertex(sideEdge2, newVert2)

    vert1Pos = cmds.pointPosition(movingVert1)
    vert2Pos = cmds.pointPosition(movingVert2)

    transX1 = newVert1.x - vert1Pos[0]
    transY1 = newVert1.y - vert1Pos[1]
    transZ1 = newVert1.z - vert1Pos[2]

    transX2 = newVert2.x - vert2Pos[0]
    transY2 = newVert2.y - vert2Pos[1]
    transZ2 = newVert2.z - vert2Pos[2]

    cmds.polyMoveVertex(movingVert1, translateX = transX1, translateY = transY1, translateZ = transZ1)
    cmds.polyMoveVertex(movingVert2, translateX = transX2, translateY = transY2, translateZ = transZ2)

    movedVertices.append(movingVert1)
    movedVertices.append(movingVert2)

    cmds.polyDelEdge(edge2, cleanVertices = True)

    return True

def matchVertices(edges):

    faces = getNonSharedFaces(edges)

    vertices = splitNames(cmds.polyListComponentConversion(edges, fromEdge = True, toVertex = True))
    vertices = list(set(vertices)) #remove duplicates

    planes = []

    for face in faces:
        planes.append(getPlaneFromFace(face))

    
    sumPoint = OpenMaya.MPoint(0.0,0.0,0.0)
    averagePoint = OpenMaya.MPoint(0.0,0.0,0.0)

    for i in range(len(planes) - 2):
        colPoint = calculateColisionPlanes(planes[0], planes[1], planes[i + 2])
        sumPoint += OpenMaya.MVector(colPoint)
        averagePoint = sumPoint / (i + 1)
        #if averagePoint.distanceTo(colPoint) > 0. :
            #cmds.error("Invalid face")
        

    for vertex in vertices:
        vertPos = cmds.pointPosition(vertex)

        transX = averagePoint.x - vertPos[0]
        transY = averagePoint.y - vertPos[1]
        transZ = averagePoint.z - vertPos[2]


        cmds.polyMoveVertex(vertex, translateX = transX, translateY = transY, translateZ = transZ)

    cmds.polyMergeVertex(vertices, distance = 0.1)
    return True


def getNonSharedFaces(edges):
    nonSharedFaces = []
    sharedFaces = []
    for edge in edges:
        edgeFaces = cmds.filterExpand(cmds.polyListComponentConversion(edge, fromEdge = True, toFace = True), sm = 34)
        for face in edgeFaces:
            if face in nonSharedFaces:
                nonSharedFaces.remove(face)
                sharedFaces.append(face)
            elif face not in sharedFaces:
                nonSharedFaces.append(face)
            
    return nonSharedFaces
        


def shorterEdgeFirst(edge1, edge2):
    if (edgeLength(edge2) < edgeLength(edge1)):
        return edge2, edge1   
    return edge1, edge2

def longerEdgeFirst(edge1, edge2):
    if (edgeLength(edge2) > edgeLength(edge1)):
        return edge2, edge1   
    return edge1, edge2

def orderPairs(edge1, edge2, edge3, edge4, otherFaces):
    longestEdge = edge1
    longestLength = 0.0
    edges = [edge1, edge2, edge3, edge4]
    for edge in edges:
        length = edgeLength(edge)
        if length > longestLength:
            longestEdge = edge
            longestLength = length
    face1, face2 = getNonSharedFaces([edge1, edge2])
    face3, face4 = getNonSharedFaces([edge3, edge4])
    if face3 in otherFaces or face4 in otherFaces:
        return edge1, edge2, edge3, edge4
    elif face1 in otherFaces or face2 in otherFaces:
        return edge3, edge4, edge1, edge2
    if longestEdge == edge1 or longestEdge == edge2:
        return edge1, edge2, edge3, edge4
    else:
        return edge3, edge4, edge1, edge2

def undoBevelFace(face, otherFaces, movedVertices):
    edges = splitNames(cmds.polyListComponentConversion(face, fromFace = True, toEdge = True))

    if len(edges) == 4:
        edgeCombos = []
        edge1 = edges[0]
        edge2 = None
        for edge in edges:
            if not edgesTouching(edge1, edge) and edge != edge1:
                if edge2:
                    cmds.error("Invalid face")
                edge2 = edge 

        edge3 = None
        edge4 = None 
        for edge in edges:
            if edgesTouching(edge1, edge):
                if not edge3:
                    edge3 = edge
                elif not edge4:
                    edge4 = edge
                else:
                    cmds.error("Invalid face")
        if not edge2 or not edge4:
            cmds.error("Invalid face")
        
        edge1, edge2, edge3, edge4 = orderPairs(edge1, edge2, edge3, edge4, otherFaces)
        
        edgeCombos.append(shorterEdgeFirst(edge1, edge2))
        edgeCombos.append(shorterEdgeFirst(edge3, edge4))
        edgeCombos.append(longerEdgeFirst(edge1, edge2))
        edgeCombos.append(longerEdgeFirst(edge3, edge4))

        for edge1, edge2 in edgeCombos:
            face1, face2 = getNonSharedFaces([edge1, edge2])
            matched = matchEdge(edge1, face1, edge2, face2, movedVertices)
            if matched:
                return
    else:
        cmds.error("faces must have 4 or 3 sides")
    cmds.error("Invalid")

    """elif len(edges) >= 3:
    matched = matchVertices(edges)
    if matched:
        return"""

def undoBevel():
    """Given selected faces, undo the bevel"""
    print("// UndoBevel //")
    movedVertices = []
    selected = cmds.ls(orderedSelection = True, flatten = True)

    if len(selected) < 1:
        return

    if '.f[' in selected[0]:
        for face in selected:
            if '.f[' not in face:
                cmds.error("Select either a number of faces, or 2 edges")

        for face in reversed(selected):
            undoBevelFace(face, selected, movedVertices)

    elif '.e[' in selected[0]:
        if len(selected) != 2 or '.e[' not in selected[1]:
            cmds.error("Select either a number of faces, or 2 edges")   
        edgeCombos = []
        edge1 = selected[0]
        edge2 = selected[1]
        print(edge1, edge2)

        edgeCombos.append(shorterEdgeFirst(edge1, edge2))
        edgeCombos.append(longerEdgeFirst(edge1, edge2))
        
        for edge1, edge2 in edgeCombos:
                face1, face2 = getNonSharedFaces([edge1, edge2])
                matched = matchEdge(edge1, face1, edge2, face2, movedVertices)
                if matched:
                    return
        cmds.error("Invalid")
    
    if len(movedVertices) > 0:
        cmds.polyMergeVertex(movedVertices, distance = 0.1)

    return


    
# Creator
def cmdCreator():
    return OpenMayaMPx.asMPxPtr( scriptedCommand() )
    
# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand( kPluginCmdName, cmdCreator )
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )