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
    split = name.split('[')
    objectName = split[0]
    numbersFull = split[1]
    result = []
    numbers = numbersFull.split(':')
    for number in numbers:
        number = number.replace(']', '')
        result.append(objectName + "[" + number + "]")
    return result

def splitNames(names):
    result = []
    for name in names:
        split = splitName(name)
        for newName in split:
            result.append(newName)
    return result

def edgeLength(edge):
    vertices = cmds.polyListComponentConversion(edge, fromEdge = True, toVertex = True)
    vertices = splitNames(vertices)
    vertex1, vertex2 = vertices[0], vertices[1]
    x1, y1, z1 = [cmds.pointPosition(vertex1)[i] for i in (0,1,2)]
    x2, y2, z2= [cmds.pointPosition(vertex2)[i] for i in (0,1,2)]
    return math.sqrt(math.pow(x1 - x2, 2.0) + math.pow(y1 - y2, 2.0) + math.pow(z1 - z2, 2.0))

def inRange(a, b, c, d, rangeVal):
    return (max(a, b, c, d) - min(a, b, c, d)) <= rangeVal


def faceAxis(face):
    print face
    faceVertices = cmds.polyListComponentConversion(face, fromFace = True, toVertex = True)
    print faceVertices
    faceVertices = splitNames(faceVertices)
    print faceVertices
    faceVertex1, faceVertex2, faceVertex3, faceVertex4 = [cmds.pointPosition(faceVertices[i]) for i in (0,1,2,3)]

    if inRange(faceVertex1[0], faceVertex2[0], faceVertex3[0], faceVertex4[0], 0.1):
        return 0
    elif inRange(faceVertex1[1], faceVertex2[1], faceVertex3[1], faceVertex4[1], 0.1):
        return 1
    elif inRange(faceVertex1[2], faceVertex2[2], faceVertex3[2], faceVertex4[2], 0.1):
        return 2
    else:
        print("invalid")
        return


def matchEdge(edge1, face1, edge2, face2):
    edge1Vertices = cmds.polyListComponentConversion(edge1, fromEdge = True, toVertex = True)
    edge2Vertices = cmds.polyListComponentConversion(edge2, fromEdge = True, toVertex = True)
    edge1Point = cmds.pointPosition(edge1Vertices[0])
    edge2Point = cmds.pointPosition(edge2Vertices[0])
    
    face1Axis = faceAxis(face1)
    face2Axis = faceAxis(face2)
    dist = edge1Point[face1Axis] - edge2Point[face1Axis]
    translate = [dist * (face1Axis == 0), dist * (face1Axis == 1), dist * (face1Axis == 2)]

    cmds.polyMoveEdge(edge2, translate = translate)

    cmds.polyDelEdge(edge1, cleanVertices = True)

    return


def undoBevel():
    selectedEdges = cmds.ls(selection = True, flatten = True)
    
    if len(selectedEdges) != 2:
        print "Select 2 edges"
        return
    
    edge1 = selectedEdges[0]
    edge2 = selectedEdges[1]

    if (edgeLength(edge2) > edgeLength(edge1)):
        edge1 = selectedEdges[1]
        edge2 = selectedEdges[0]

    edge1Faces = cmds.polyListComponentConversion(edge1, fromEdge = True, toFace = True)
    edge2Faces = cmds.polyListComponentConversion(edge2, fromEdge = True, toFace = True)

    edge1Faces = splitNames(edge1Faces)
    edge2Faces = splitNames(edge2Faces)

    sharedFace = edge1Faces[0]

    if sharedFace != edge2Faces[0] and sharedFace != edge2Faces[1]:
        sharedFace = edge1Faces[1]
        if sharedFace != edge2Faces[0] and sharedFace != edge2Faces[1]:
            print "edges do not share face"
            return

    face1 = edge1Faces[0]
    face2 = edge2Faces[0]

    if face1 == sharedFace:
        face1 = edge1Faces[1]

    if face2 == sharedFace:
        face2 = edge2Faces[1]

    print edge1
    print edge1Faces
    print edge2 
    print edge2Faces
    print sharedFace

    matchEdge(edge1, face1, edge2, face2)

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