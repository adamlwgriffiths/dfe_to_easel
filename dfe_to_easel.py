from __future__ import absolute_import, print_function, division, unicode_literals
import xml.etree.ElementTree as ET
import json
import os

def get_sprite(sprites, name):
    # find the sprite in our sprites list
    # root dir is always /
    full_path = ['/'] + name.split('/')
    path = full_path[:-1]
    spr_name = path[-1]

def parse_sprites(_sprites):
    def walk_dir(node, path):
        # walk dirs
        for dir in node.findall('./dir'):
            name = dir.get('name')
            full_path = path + '/' + name
            if path == '/':
                full_path = full_path[1:]
            for x in walk_dir(dir, full_path):
                yield x

        # walk sprites in this dir
        for spr in node.findall('./spr'):
            name = spr.get('name')
            full_path = path + '/' + name
            if path == '/':
                full_path = full_path[1:]
            print('Found frame',full_path)

            x = int(spr.get('x'))
            y = int(spr.get('y'))
            w = int(spr.get('w'))
            h = int(spr.get('h'))

            # always refer to image 0
            # x/y offset, default to 0
            index, regX, regY = 0, 0, 0

            frame = [x, y, w, h, 0, regX, regY]

            yield full_path, frame

    # parse the sprites and generate a list of frames
    # make a list and a dict with name:index pairs for referencing
    frames = []
    frame_lookup = {}

    # recurse down the path
    definitions = _sprites.find('definitions')
    root = definitions.find('./')
    for path, frame in walk_dir(root, '/'):
        frame_lookup[path] = len(frames)
        frames.append(frame)

    return frames, frame_lookup

def parse_anims(_frames, frame_lookup, _anim):
    def walk_anims():
        for anim in _anim.findall('./anim'):
            name = anim.get('name')
            frames = []
            frame_count = 0
            speed = 0.
            print('Processing',name)
            for cell in anim.findall('./cell'):
                speed += int(cell.get('delay'))

                # get the first sprite ignore the others
                spr = cell.find('./spr')
                x_offset = int(spr.get('x'))
                y_offset = int(spr.get('y'))

                sprite_name = spr.get('name')
                # find the sprite in our sprites list
                frame = frame_lookup[sprite_name]
                frames.append(frame)

                # update the x/y offset
                _frames[frame][5] = x_offset
                _frames[frame][6] = y_offset

                frame_count += 1

            # average out the frame speed
            #if not speed:
            #    speed = 1.
            #speed /= frame_count
            #speed = 1. / speed
            speed = 1

            yield name, frames, speed

    anims = {}
    for name, frames, speed in walk_anims():
        anim = {
            'frames': frames,
            'speed': speed,
        }
        anims[name] = anim

    return anims

def parse(sprites, anim, framerate=20):
    frames, frame_lookup = parse_sprites(sprites)
    animations = parse_anims(frames, frame_lookup, anim)

    image = sprites.get('name')
    data = {
        'framerate': framerate,
        'images': [image],
        'frames': frames,
        'animations': animations
    }

    # return json
    return data

def load_files(anim_path):
    with open(anim_path, 'r') as f:
        anim = f.read()
    anim_xml = ET.fromstring(anim)

    # get the sprite sheet
    spritesheet = anim_xml.get('spriteSheet')
    sprites_path = os.path.join(os.path.dirname(anim_path), spritesheet)
    with open(sprites_path, 'r') as f:
        sprites = f.read()
    sprites_xml = ET.fromstring(sprites)

    return sprites_xml, anim_xml

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert darkFunction Editor animations to Easel json blobs")
    parser.add_argument("anim", help="The darkFunction Editor .anim file")
    parser.add_argument("output", help="The json file to save to")
    parser.add_argument("-f", "--framerate", default=20, type=int, help="The framerate to use")
    args = parser.parse_args()

    anim = os.path.abspath(args.anim)
    sprites_xml, anim_xml = load_files(anim)
    result = parse(sprites_xml, anim_xml, args.framerate)

    output = os.path.abspath(args.output)
    with open(args.output, 'w') as f:
        f.write(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    main()
