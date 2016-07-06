#!/usr/bin/env python

import os
import shutil
import subprocess
import sys

__author__ = 'darklinden'

EXCLUDE_START = [
    '--',
    'layout',
    "result['animation']:",
    'localFrame:setTween',

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
    'localFrame = ccs.ScaleFrame:create()'
]


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

    result = ''

    f = open(path, "rb")

    line = f.readline()

    lastRate = '0.0'
    stIdx = 0 # scaleTo Index
    sqIdx = 0 # sequence Index
    ftIdx = 0 # fadeTo Index
    afIdx = 0 # animateFrame Index

    while len(line) > 0:
        line = line.strip()

        isExclude = False

        for value in EXCLUDE_START:
            if line.startswith(value):
                isExclude = True
                break

        for value in EXCLUDE_LINE:
            if line == str(value).strip():
                isExclude = True
                break

        if not isExclude:
            if 'setBlendFunc' in line:
                line = line.replace('({src = ', '(')
                line = line.replace(', dst = ', ', ')
                line = line.replace('})', ')')
            elif line == 'local AlphaTimeline = ccs.Timeline:create()':
                # fade start
                line = '-- cc.FadeTo'
            elif line.startswith('AlphaTimeline:setNode('):
                # fade end
                node = line[len('AlphaTimeline:setNode('):]
                node = node[:-1]

                x = 0
                line = "local sq" + str(sqIdx) + " = cc.Sequence:create("
                while x < ftIdx:
                    line += "ft" + str(x) + ", "
                    x = x + 1
                line = line[:-2]
                line += ")\n" + node + ":runAction(sq" + str(sqIdx) + ")"
                ftIdx = 0
                sqIdx += 1
            elif line == 'local FileDataTimeline = ccs.Timeline:create()':
                line = '-- spriteFrames\n'
                line += 'local animFrames' + str(afIdx) + ' = {}\n'
                line += 'local frame' + str(afIdx) + " = nil"


            elif line.startswith('FileDataTimeline:setNode('):
                # sprite frame end
                node = line[len('FileDataTimeline:setNode('):]
                node = node[:-1]

                line = 'local animation' + str(afIdx) + ' = cc.Animation:createWithSpriteFrames('
                line += 'animFrames' + str(afIdx) + ', rate)\n'
                line += 'local animate' + str(afIdx) + ' = cc.Animate:create(animation' + str(afIdx) + ')\n'
                line += node + ":runAction(animate" + str(afIdx) + ")"

            elif line == 'local ScaleTimeline = ccs.Timeline:create()':
                # scale start
                line = '-- cc.ScaleTo'
            elif line.startswith('ScaleTimeline:setNode('):
                # scale end
                node = line[len('ScaleTimeline:setNode('):]
                node = node[:-1]

                x = 0
                line = "local sq" + str(sqIdx) + " = cc.Sequence:create("
                while x < stIdx:
                    line += "st" + str(x) + ", "
                    x = x + 1
                line = line[:-2]
                line += ")\n" + node + ":runAction(sq" + str(sqIdx) + ")"
                stIdx = 0
                sqIdx += 1
            elif line.startswith('localFrame:setFrameIndex'):
                # print(line)
                rate = line[len('localFrame:setFrameIndex('):]
                rate = rate[:-1]
                if rate == '0':
                    lastRate = '0.0'

                if lastRate == '0.0':
                    line = "rate = " + rate + ".0"
                else:
                    line = "rate = (" + rate + ".0 - " + lastRate + ") / timeRate"

                lastRate = rate + ".0"
            elif line.startswith('localFrame:setScaleX('):
                scaleX = line[len('localFrame:setScaleX('):]
                scaleX = scaleX[:-1]

                nextLine = f.readline()
                nextLine = nextLine.strip()
                scaleY = nextLine[len('localFrame:setScaleY('):]
                scaleY = scaleY[:-1]

                line = "local st" + str(stIdx) + " = cc.ScaleTo:create(rate, " + scaleX + ", " + scaleY + ")"
                stIdx = stIdx + 1

            elif line.startswith('localFrame:setTextureName('):
                frameName = line[len('localFrame:setTextureName('):]
                frameName = frameName[:-1]

                line = 'frame = cc.SpriteFrameCache:getInstance():getSpriteFrame(' + frameName + ')\ntable.insert(animFrames' + str(afIdx) + ', frame)'
            elif line.startswith('localFrame:setAlpha('):
                alpha = line[len('localFrame:setAlpha('):]
                alpha = alpha[:-1]

                line = "local ft" + str(ftIdx) + " = cc.FadeTo:create(rate, " + alpha + ")"
                ftIdx = ftIdx + 1

            elif line == "result['animation'] = ccs.ActionTimeline:create()":
                line = 'local timeRate = 12.0\nlocal rate = 0.0'


            result += line + '\n'

        line = f.readline()

    f.close()

    result = result.strip()

    new_path = path[:path.rfind('.')] + "_x.lua"

    fw = open(new_path, "wb")
    fw.write(result)
    fw.close()

    print("Done")

__maim__()