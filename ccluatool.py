#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'darklinden'

import os
import shutil
import subprocess
import sys
import json

# for installation
def run_cmd(cmd):
    # print("run cmd: " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out

def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    print("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])

# for
EXCLUDE_START = [
    '--',
    'layout',
    "result['animation']:",
    'localFrame:setTween'
]

EXCLUDE_LINE = [
    'local luaExtend = require "LuaExtend"',
    'local layout = nil',
    'local localLuaFile = nil',
    'local innerCSD = nil',
    'local innerProject = nil',
    'local localFrame = nil',
    'local Result = {}',
    'function Result.create(callBackProvider)',
    'local result={}',
    'setmetatable(result, luaExtend)',
    "result['root'] = Node",
    'return result;',
    'end',
    'return Result',
    'FileDataTimeline:addFrame(localFrame)',
    'AlphaTimeline:addFrame(localFrame)',
    'ScaleTimeline:addFrame(localFrame)',
    'localFrame = ccs.TextureFrame:create()',
    'localFrame = ccs.AlphaFrame:create()',
    'localFrame = ccs.ScaleFrame:create()',
    "result['animation'] = ccs.ActionTimeline:create()"
]

STATIC_NUM = 0
def act_uniqueue_number():
    global STATIC_NUM
    STATIC_NUM = STATIC_NUM + 1
    return str(STATIC_NUM)

def isNodeStart(line):
    checkLine = line.strip(" \t\n\r")
    if checkLine == "--Create Node":
        return True
    return False

def isAnimationStart(line):
    checkLine = line.strip(" \t\n\r")
    if checkLine == "--Create Animation":
        return True
    return False

def isExclude(line):
    ret = False
    tmp = line.strip(' \t\n\r')

    for value in EXCLUDE_START:
        if tmp.startswith(value):
            ret = True
            break

    for value in EXCLUDE_LINE:
        if tmp == str(value).strip():
            ret = True
            break

    return ret

def push_action(nodeActions, act_str, node):
    if nodeActions.has_key(node):
        na = nodeActions[node]
    else:
        na = []
    na.append(act_str)
    nodeActions[node] = na

def deal_with_lua(path):

    f = open(path, "rb")
    result = ''

    actionObj = {}
    nodeActions = []
    allActions = {}

    isNode = False
    isAnimation = False

    animTypeNone = "none"
    animTypeFade = "fade"
    animTypeSprite = "spriteframe"
    animTypeScale = "scale"
    animTypePosition = "position"
    animTypeRotation = "rotation"
    animTypeColor = "color"
    animTypeAnchorPoint = "anchorPoint"
    animTypeBlendFunc = "blendFunc"
    animTypeVisibleForFrame = "visibleForFrame"
    
    animType = animTypeNone

    framesPerSecond = 0.0
    frameCount = 0

    lastAnimFrameIndex = 0

    while True:

        # get one new line
        line = f.readline()
        if line == '':
            # reach the end of the file
            break

        line = line.strip(" \t\r\n")

        if not isNode:
            isNode = isNodeStart(line)

        if not isAnimation:
            isAnimation = isAnimationStart(line)
            if isAnimation:
                isNode = False

        if isNode:
            # print("node line: [" + line + "]")
            # deal with blendfunc for cocos2d-x 3.3
            if 'setBlendFunc' in line:
                line = line.replace('({src = ', '(')
                line = line.replace(', dst = ', ', ')
                line = line.replace('})', ')')

            if isExclude(line):
                pass
            else:
                result += line + "\n"

        elif isAnimation:
            # print("animation line: [" + line + "]")

            if line.startswith("result['animation']:setDuration("):
                strFrameCount = line[len("result['animation']:setDuration("):]
                strFrameCount = strFrameCount[:-1]
                frameCount = float(strFrameCount)
                result += "local frameCount = " + str(frameCount) + "\n"
            elif line.startswith("result['animation']:setTimeSpeed("):
                strFramesPerSecond = line[len("result['animation']:setTimeSpeed("):]
                strFramesPerSecond = strFramesPerSecond[:-1]
                framesPerSecond = float(strFramesPerSecond) * 60
                result += "local framesPerSecond = " + str(framesPerSecond) + "\n\n"
            # fade action start
            elif line == 'local AlphaTimeline = ccs.Timeline:create()':
                # result += '-- cc.FadeTo\n'
                animType = animTypeFade
                lastAnimFrameIndex = 0
                nodeActions = []
            # sprite frame action start
            elif line == 'local FileDataTimeline = ccs.Timeline:create()':
                # result += '-- spriteFrames\n'
                animType = animTypeSprite
                lastAnimFrameIndex = 0
                nodeActions = []
            # scale action start
            elif line == 'local ScaleTimeline = ccs.Timeline:create()':
                # result += '-- cc.ScaleTo\n'
                animType = animTypeScale
                lastAnimFrameIndex = 0
                nodeActions = []
            # position action start
            elif line == 'local PositionTimeline = ccs.Timeline:create()':
                # result += '-- cc.MoveTo\n'
                animType = animTypePosition
                lastAnimFrameIndex = 0
                nodeActions = []
            # rotation action start
            elif line == 'local RotationSkewTimeline = ccs.Timeline:create()':
                # result += '-- cc.RotateTo\n'
                animType = animTypeRotation
                lastAnimFrameIndex = 0
                nodeActions = []
            elif line == 'local CColorTimeline = ccs.Timeline:create()':
                # result += '-- color\n'
                animType = animTypeColor
                lastAnimFrameIndex = 0
                nodeActions = []
            elif line == 'localFrame = ccs.AnchorPointFrame:create()':
                # result += '-- anchorPoint\n'
                animType = animTypeAnchorPoint
                lastAnimFrameIndex = 0
                nodeActions = []
            elif line == 'local BlendFuncTimeline = ccs.Timeline:create()':
                # result += '-- BlendFuncTimeline\n'
                animType = animTypeBlendFunc
                lastAnimFrameIndex = 0
                nodeActions = []
            elif line == 'local VisibleForFrameTimeline = ccs.Timeline:create()':
                # result += '-- VisibleForFrame\n'
                animType = animTypeVisibleForFrame
                lastAnimFrameIndex = 0
                nodeActions = []
                
            # frame start
            elif line.startswith('localFrame:setFrameIndex'):
                # print(line)
                rate = line[len('localFrame:setFrameIndex('):]
                rate = rate[:-1]

                if rate == 0:
                    animFrameLen = 0
                else:
                    animFrameLen = float(int(rate) - lastAnimFrameIndex) / framesPerSecond

                animFrameLen = float("{0:.2f}".format(animFrameLen))
                lastAnimFrameIndex = int(rate)
                actionObj = {}
                # if animFrameLen < 0:
                #     pass
                actionObj["animFrameLen"] = animFrameLen
            # frame end
            elif line.find("Timeline:addFrame(") != -1:
                nodeActions.append(actionObj)
            # action end
            elif line.find('Timeline:setNode(') != -1:
                node = line[line.find('Timeline:setNode(') + len('Timeline:setNode('):]
                node = node[:-1]

                if animType != animTypeColor and animType != animTypeAnchorPoint and animType != animTypeBlendFunc and animType != animTypeVisibleForFrame:
                    actions = allActions.get(node, {})
                    actions[animType] = nodeActions
                    allActions[node] = actions
                    
            # alpha action
            elif line.startswith('localFrame:setAlpha('):
                alpha = line[len('localFrame:setAlpha('):]
                alpha = alpha[:-1]
                
                actionObj["animAlpha"] = int(alpha)
            # scale X
            elif line.startswith('localFrame:setScaleX('):
                scaleX = line[len('localFrame:setScaleX('):]
                scaleX = scaleX[:-1]

                actionObj["animScaleX"] = float(scaleX)
            # scale Y
            elif line.startswith('localFrame:setScaleY('):
                scaleY = line[len('localFrame:setScaleY('):]
                scaleY = scaleY[:-1]

                actionObj["animScaleY"] = float(scaleY)
            # textureName
            elif line.startswith('localFrame:setTextureName("'):
                textureName = line[len('localFrame:setTextureName("'):]
                textureName = textureName[:-2]

                actionObj["animTextureName"] = textureName
            # pos X
            elif line.startswith('localFrame:setX('):
                posX = line[len('localFrame:setX('):]
                posX = posX[:-1]

                actionObj["animPosX"] = float(posX)
            # pos Y
            elif line.startswith('localFrame:setY('):
                posY = line[len('localFrame:setY('):]
                posY = posY[:-1]

                actionObj["animPosY"] = float(posY)
            # rotationX
            elif line.startswith('localFrame:setSkewX('):
                rotationX = line[len('localFrame:setSkewX('):]
                rotationX = rotationX[:-1]

                actionObj["animRotationX"] = float(rotationX)
            # rotation Y
            elif line.startswith('localFrame:setSkewY('):
                rotationY = line[len('localFrame:setSkewY('):]
                rotationY = rotationY[:-1]

                actionObj["animRotationY"] = float(rotationY)
        else:
            pass

    # print ("all actions:")
    # print(json.dumps(allActions))

    for node in allActions:
        result += "-- " + node + " animations\n"
        actions = allActions[node]
        act_in_spawn = []
        # single node actions
        for animKey in actions:
            animActs = actions[animKey]
            if animKey == animTypeFade:
                act_in_sequence = []
                for animObj in animActs:
                    num = act_uniqueue_number()
                    if animObj["animFrameLen"] == 0:
                        result += "local anim" + num + " = cc.CallFunc:create(function() " + node + ":setOpacity(" + str(animObj["animAlpha"]) + ") end)\n"
                    else:
                        result += "local anim" + num + " = cc.FadeTo:create(" + str(animObj["animFrameLen"]) + ", " + str(animObj["animAlpha"]) + ")\n"
                    act_in_sequence.append("anim" + num)
                if len(act_in_sequence) > 1:
                    num = act_uniqueue_number()
                    act_str = ', '.join(act_in_sequence)
                    result += "local anim" + num + " = cc.Sequence:create(" + act_str + ")\n"
                    act_in_spawn.append("anim" + num)
                else:
                    act_in_spawn.append(act_in_sequence[0])

            elif animKey == animTypeScale:
                act_in_sequence = []
                for animObj in animActs:
                    num = act_uniqueue_number()
                    if animObj["animFrameLen"] == 0:
                        result += "local anim" + num + " = cc.CallFunc:create(function() " + \
                                  node + ":setScale(" + str(animObj["animScaleX"]) + ", " + str(animObj["animScaleY"]) + ") end)\n"
                    else:
                        result += "local anim" + num + " = cc.ScaleTo:create(" + \
                                  str(animObj["animFrameLen"]) + ", " + str(animObj["animScaleX"]) + ", " + str(animObj["animScaleY"]) + ")\n"
                    act_in_sequence.append("anim" + num)
                if len(act_in_sequence) > 1:
                    num = act_uniqueue_number()
                    act_str = ', '.join(act_in_sequence)
                    result += "local anim" + num + " = cc.Sequence:create(" + act_str + ")\n"
                    act_in_spawn.append("anim" + num)
                else:
                    act_in_spawn.append(act_in_sequence[0])

            elif animKey == animTypeSprite:
                # frames_table = 'animFrames' + act_uniqueue_number()
                # result += 'local ' + frames_table + ' = {}\n'
                # for animObj in animActs:
                #     frame_name = 'frame' + act_uniqueue_number()
                #     result += 'local ' + frame_name + ' = cc.SpriteFrameCache:getInstance():getSpriteFrame("' + animObj["animTextureName"] + '")\n'
                #     result += 'if ' + frame_name + ' ~= nil then\ntable.insert(' + frames_table + ', ' + frame_name + ')\nend\n'
                # 
                # animation_name = 'animation' + act_uniqueue_number()
                # result += 'local ' + animation_name + ' = cc.Animation:createWithSpriteFrames(' + frames_table + ', ' + str(animActs[0]["animFrameLen"]) + ')\n'
                # animate_name = 'animate' + act_uniqueue_number()
                # result += 'local ' + animate_name + ' = cc.Animate:create(' + animation_name + ')\n'
                # act_in_spawn.append(animate_name)
                
                act_in_sequence = []
                for animObj in animActs:
                    num = act_uniqueue_number()
                    result += 'local delay' + num + ' = cc.DelayTime:create(' + str(animObj["animFrameLen"]) + ')\n'
                    act_in_sequence.append("delay" + num)
                    result += 'local anim' + num + ' = cc.CallFunc:create(function ()\n    ' + node + ':setSpriteFrame("' + str(animObj["animTextureName"]) + '")\nend)\n'
                    act_in_sequence.append("anim" + num)

                if len(act_in_sequence) > 1:
                    num = act_uniqueue_number()
                    act_str = ', '.join(act_in_sequence)
                    result += "local anim" + num + " = cc.Sequence:create(" + act_str + ")\n"
                    act_in_spawn.append("anim" + num)
                else:
                    act_in_spawn.append(act_in_sequence[0])
                
            elif animKey == animTypePosition:
                act_in_sequence = []
                for animObj in animActs:
                    num = act_uniqueue_number()
                    if animObj["animFrameLen"] == 0:
                        result += "local anim" + num + " = cc.CallFunc:create(function() " + \
                                  node + ":setPosition(" + str(animObj["animPosX"]) + ", " + \
                                  str(animObj["animPosY"]) + ") end)\n"
                    else:
                        result += "local anim" + num + " = cc.MoveTo:create(" + \
                                  str(animObj["animFrameLen"]) + ", cc.p(" + str(animObj["animPosX"]) + ", " + str(
                            animObj["animPosY"]) + "))\n"
                    act_in_sequence.append("anim" + num)
                if len(act_in_sequence) > 1:
                    num = act_uniqueue_number()
                    act_str = ', '.join(act_in_sequence)
                    result += "local anim" + num + " = cc.Sequence:create(" + act_str + ")\n"
                    act_in_spawn.append("anim" + num)
                else:
                    act_in_spawn.append(act_in_sequence[0])

            elif animKey == animTypeRotation:
                act_in_sequence = []
                for animObj in animActs:
                    num = act_uniqueue_number()
                    if animObj["animFrameLen"] == 0:
                        result += "local anim" + num + " = cc.CallFunc:create(function() \n" + \
                                  node + ":setRotationSkewX(" + str(animObj["animRotationX"]) + ")\n" + \
                                  node + ":setRotationSkewY(" + str(animObj["animRotationY"]) + ")\n end)\n"
                    else:
                        result += "local anim" + num + " = cc.RotateTo:create(" + \
                                str(animObj["animFrameLen"]) + ", " + str(animObj["animRotationX"]) + ", " + str(animObj["animRotationY"]) + ")\n"
                    act_in_sequence.append("anim" + num)
                if len(act_in_sequence) > 1:
                    num = act_uniqueue_number()
                    act_str = ', '.join(act_in_sequence)
                    result += "local anim" + num + " = cc.Sequence:create(" + act_str + ")\n"
                    act_in_spawn.append("anim" + num)
                else:
                    act_in_spawn.append(act_in_sequence[0])

        if len(act_in_spawn) > 1:
            num = act_uniqueue_number()
            act_str = ', '.join(act_in_spawn)
            result += "local anim" + num + " = cc.Spawn:create(" + act_str + ")\n"
            result += node + ":runAction(anim" + num + ")\n\n"
        else:
            result += node + ":runAction(" + act_in_sequence[0] + ")\n\n"

    f.close()
    
    totalLen = float("{0:.2f}".format(frameCount / framesPerSecond)) + 0.5
    
    num1 = act_uniqueue_number()
    result += "local delay" + num1 + " = cc.DelayTime:create(" + str(totalLen) + ")\n"
    num2 = act_uniqueue_number()
    result += "local end" + num2 + " = cc.CallFunc:create(function()\n    print('animation ended')\nend)\n"
    result += "Node:runAction(cc.Sequence:create(delay" + num1 + ", end" + num2 + "))"

    result = result.strip()

    new_path = path[:path.rfind('.')] + "_x.lua"

    fw = open(new_path, "wb")
    fw.write(result)
    fw.close()

def __maim__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("ccluatool.py", "/usr/local/bin")
        return

    path = ""
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        return

    if len(path) == 0:
        print("using ccluatool [lua-path] to strip lua ")
        return

    if not str(path).startswith('/'):
        path = os.path.join(os.getcwd(), path)

    deal_with_lua(path)

    print("Done")

__maim__()