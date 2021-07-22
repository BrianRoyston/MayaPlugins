import sys
import os
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from maya import cmds

# Brian Royston
# 2021


kPluginCmdName = "createDisney"

BASE_COLOR = 0
EMIT_COLOR = 1
METALLIC = 2
SPECULAR = 3
ROUGHNESS = 4
BUMP_NORMAL = 5
DISPLACEMENT = 6 

NUM_IMAGE_TYPES = 7

IMAGE_KEY_WORDS = {
    BASE_COLOR : {"col", "diff"},
    EMIT_COLOR : {"emit", "emission", "glow"},
    METALLIC : {"metal"},
    SPECULAR : {"specular"},
    ROUGHNESS : {"rough"},
    BUMP_NORMAL : {"bump", "nor"},
    DISPLACEMENT : {"disp"},
}

IMAGE_TYPE_NAMES = {
    BASE_COLOR : "Base",
    EMIT_COLOR : "Emit",
    METALLIC : "Metal",
    SPECULAR : "Specular",
    ROUGHNESS : "Rough",
    BUMP_NORMAL : "Bump",
    DISPLACEMENT : "Disp",
}

# Command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
        
    # Invoked when the command is run.
    def doIt(self,argList):
        build_network()

def create_place2d(name):
    place2d_node = cmds.shadingNode("place2dTexture", name=name, asTexture=True) # creates node
    return place2d_node

def create_file(name, filepath, place2d):
    file_node = cmds.shadingNode("file", name=name, asTexture=True) # creates node

    cmds.setAttr("%s.fileTextureName" % file_node, filepath, type = "string") #sets filepath

    # connecting it to the place2dd
    cmds.connectAttr("%s.coverage" % place2d, "%s.coverage" % file_node)
    cmds.connectAttr("%s.mirrorU" % place2d, "%s.mirrorU" % file_node)
    cmds.connectAttr("%s.mirrorV" % place2d, "%s.mirrorV" % file_node)
    cmds.connectAttr("%s.noiseUV" % place2d, "%s.noiseUV" % file_node)
    cmds.connectAttr("%s.offset" % place2d, "%s.offset" % file_node)
    cmds.connectAttr("%s.outUV" % place2d, "%s.uvCoord" % file_node)
    cmds.connectAttr("%s.outUvFilterSize" % place2d, "%s.uvFilterSize" % file_node)
    cmds.connectAttr("%s.repeatUV" % place2d, "%s.repeatUV" % file_node)
    cmds.connectAttr("%s.rotateFrame" % place2d, "%s.rotateFrame" % file_node)
    cmds.connectAttr("%s.rotateUV" % place2d, "%s.rotateUV" % file_node)
    cmds.connectAttr("%s.stagger" % place2d, "%s.stagger" % file_node)
    cmds.connectAttr("%s.translateFrame" % place2d, "%s.translateFrame" % file_node)
    cmds.connectAttr("%s.vertexCameraOne" % place2d, "%s.vertexCameraOne" % file_node)
    cmds.connectAttr("%s.vertexUvOne" % place2d, "%s.vertexUvOne" % file_node)
    cmds.connectAttr("%s.vertexUvThree" % place2d, "%s.vertexUvThree" % file_node)
    cmds.connectAttr("%s.vertexUvTwo" % place2d, "%s.vertexUvTwo" % file_node)
    cmds.connectAttr("%s.wrapU" % place2d, "%s.wrapU" % file_node)
    cmds.connectAttr("%s.wrapV" % place2d, "%s.wrapV" % file_node)
    return file_node

def create_lambert(name):
    lambert = cmds.shadingNode("lambert", name=name, asShader=True)
    return lambert

def create_disney(name):
    material = cmds.shadingNode("PxrDisney", name=name, asShader=True) # creates node
    lambert = create_lambert("%s_Lambert" %name)
    sg = cmds.sets(name="%sSG" % name, empty=True, renderable=True, noSurfaceShader=True) # creates SG to attatch to
    cmds.connectAttr("%s.outColor" % lambert, "%s.surfaceShader" % sg) # attaches to SG
    cmds.connectAttr("%s.outColor" % material, "%s.rman__surface" % sg) # attaches to SG
    return material, sg 


def link_file(sg, file_node, disney_node, image_type, fileName):
    if image_type is BASE_COLOR:
        cmds.connectAttr("%s.outColor" % file_node, "%s.baseColor" % disney_node)
    elif image_type is EMIT_COLOR:
        cmds.connectAttr("%s.outColor" % file_node, "%s.emitColor" % disney_node)
    elif image_type is METALLIC: 
        cmds.connectAttr("%s.outAlpha" % file_node, "%s.metallic" % disney_node)
    elif image_type is SPECULAR: 
        cmds.connectAttr("%s.outAlpha" % file_node, "%s.specular" % disney_node)
    elif image_type is ROUGHNESS: 
        cmds.connectAttr("%s.outAlpha" % file_node, "%s.roughness" % disney_node)
    elif image_type is BUMP_NORMAL:  
        cmds.connectAttr("%s.resultN" % file_node, "%s.bumpNormal" % disney_node)   
    elif image_type is DISPLACEMENT: 
        disp = cmds.shadingNode("PxrDisplace", name= "%s_Disp" % fileName, asShader=True) # creates node
        cmds.connectAttr("%s.outAlpha" % file_node, "%s.dispScalar" % disp)    
        cmds.setAttr("%s.dispAmount" % disp, 0.1) 
        cmds.connectAttr("%s.outColor" % disp, "%s.displacementShader" % sg) 

def build_network():
    filepath = cmds.fileDialog2(caption = "Select the folder of the PBR", okCaption = "Select", fileMode = 2, startingDirectory = cmds.workspace(rd =True, q=True, dir=True ))[0]
    fileName = filepath[filepath.rfind("/"):]
    print(filepath)
    print(fileName)
    place2d_node = create_place2d("%s_Place2D" % fileName)
    disney_node, sg = create_disney(fileName)
    for file in os.listdir(filepath):
        if file.endswith(".tex"):
            continue
        best_image_type = -1
        largest_index = -1
        for image_type in range(NUM_IMAGE_TYPES):
            for keyWord in IMAGE_KEY_WORDS[image_type]:  
                indexFound = file.lower().find(keyWord)       
                if indexFound > largest_index:
                    best_image_type = image_type
                    largest_index = indexFound
                    continue     
        if best_image_type >= 0:
            if best_image_type == BUMP_NORMAL:
                file_node =  cmds.shadingNode("PxrBump", name= "%s_Bump" % fileName, asTexture=True) # creates node
                cmds.setAttr("%s.filename" % file_node, filepath + "/" + file, type = "string") 
                cmds.setAttr("%s.scale" % file_node, 0.1) 
            else:
                file_node = create_file(fileName + "_File_" + IMAGE_TYPE_NAMES[best_image_type], filepath + "/" + file, place2d_node)
            link_file(sg, file_node, disney_node, best_image_type, fileName)


    
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