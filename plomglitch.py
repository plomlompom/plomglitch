#!/usr/bin/env python3
#-*- eval: (auto-fill-mode 1); fill-column: 79; -*-
import pygame
import numpy
import time
import sys
import os
HEXDIGITS = '0123456789ABCDEF'
OPCODES = 'abcdefghijklmnopqrstuvwxyzGHIJKLMNOPQRSTUVWXYZ'
MAXINT = 0xFFFFFFFF


frequency = 8000  # samples per second
audio_bit_depth = 8  # bit size of samples
num_channels = 1  # mono
buffer_size = 256  # how many samples to buffer
pygame.mixer.pre_init(frequency, audio_bit_depth, num_channels, buffer_size)
# The user will define the buffer, that is, the samples / curve of one
# buffer_size/frequency of a second.


class Melody:
    def __init__(self, melody_string):
        self.lines = melody_string.split('!')
        self.tokens = self._tokenize(self.lines[1:])
        self.stack = [0] * 256
        self.tosp = 0

    def _tokenize(self, lines):
        tokens = []
        for i, line in enumerate(lines):
            is_number = False
            for char in line:
                if char in HEXDIGITS and is_number:
                    tokens[-1] += char
                elif char != '.':
                    tokens.append(char)
                is_number = char in HEXDIGITS
        return tokens

    def compute(self, t):

        def push(value):
            self.tosp += 1
            if self.tosp == 256:
                self.tosp = 0
            self.stack[self.tosp] = value & MAXINT

        def pop():
            value = self.stack[self.tosp]
            self.tosp -= 1
            if self.tosp == -1:
                self.tosp = 255
            return value

        for token in self.tokens: 
            if not token in OPCODES:
                push(int(token, 16))
            elif token == 'a':  # T
                push(t)
            elif token == 'b':  # PUT 
                v1 = self.tosp
                v2 = v1 % 256
                v3 = v2 + 1
                if self.tosp < 255:
                    v4 = self.tosp + 1
                else:
                    v4 = self.tosp + 1 - 256
                v4_pos = self.tosp - v3 + (self.tosp >= v3) * 256
                self.stack[v4_pos] = v4
                pop()
            elif token == 'c':  # DROP
                pop()
            elif token == 'd':  # MUL
                v1 = pop()
                v2 = pop()
                push((v1 * v2))
            elif token == 'e':  # DIV
                v1 = pop()
                v2 = pop()
                push(0 if v1 == 0 else int(v2 / v1))
            elif token == 'f':  # ADD 
                v1 = pop()
                v2 = pop()
                v3 = v2 + v1
                push(v3)
            elif token == 'g':  # SUB 
                v1 = pop()
                v2 = pop()
                v3 = v2 - v1
                push(v3)
            elif token == 'h':  # MOD
                v1 = pop()
                v2 = pop()
                push(0 if v1 == 0 else int(v2 % v1))
            elif token == 'j':  # LSHIFT
                v1 = pop()
                v2 = pop()
                v3 = v2 << v1 if v1 < 32 else 0
                push(v3)
            elif token == 'k':  # RSHIFT
                v1 = pop()
                v2 = pop()
                v3 = v2 >> v1 if v1 < 32 else 0
                push(v3)
            elif token == 'l':  # AND
                v1 = pop()
                v2 = pop()
                v3 = v1 & v2
                push(v3)
            elif token == 'm':  # OR
                v1 = pop()
                v2 = pop()
                v3 = v1 | v2
                push(v3)
            elif token == 'n':  # XOR
                v1 = pop()
                v2 = pop()
                v3 = v1 ^ v2
                push(v3)
            elif token == 'o':  # NOT
                v1 = pop()
                v2 = ~v1
                push(v2)
            elif token == 'p':  # DUP
                v1 = pop()
                push(v1)
                push(v1)
            elif token == 'q':  # PICK
                v1 = self.stack[self.tosp]
                v2 = v1 + 1
                v3 = v2 % 256
                v4_pos = self.tosp - v3 + (self.tosp < v3) * 256
                v4 = self.stack[v4_pos]
                pop()
                push(v4)
            elif token == 'r':  # SWAP 
                v1 = pop()
                v2 = pop()
                push(v1)
                push(v2)
            elif token == 's':  # LT 
                v1 = pop()
                v2 = pop()
                push(MAXINT if v2 < v1 else 0)
            elif token == 't':  # GT 
                v1 = pop()
                v2 = pop()
                push(MAXINT if v2 > v1 else 0)
            elif token == 'u':  # EQ
                v1 = pop()
                v2 = pop()
                push(MAXINT if v2 == v1 else 0)
        result = self.stack[self.tosp] & 0xFF
        return result


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Plom\'s glitcher')
    parser.add_argument('-f', dest='glitch_file_path', action='store',
                        help='text file containing glitch code')
    parser.add_argument('-d', dest='display', action='store_true',
                        help='display waveform')
    parser.add_argument('glitch_string', action='store', nargs='?',
                        help='glitch code')
    return parser, parser.parse_args()


def draw(screen, buf):
    background_color = (0, 0, 0)
    foreground_color = (255, 255, 255)
    lowest_line = 255
    screen.fill(background_color)
    for x, y in enumerate(buf):
        y = frame_size - y - 1
        pygame.draw.line(screen, foreground_color, (x, lowest_line), (x, y))
    pygame.display.flip()


argparser, args = parse_args()
if args.glitch_file_path:
    if not os.path.isfile(args.glitch_file_path):
        print('File not found.')
        sys.exit(1)
    with open(args.glitch_file_path, 'r') as f:
        lines = f.readlines()
    melody = Melody(lines[0].rstrip())
elif args.glitch_string:
    melody = Melody(args.glitch_string)
else:
    argparser.print_help()
    sys.exit(1)
frame_size = 2 ** audio_bit_depth
pygame.init()
channel = pygame.mixer.find_channel()
size = width, height = buffer_size, frame_size
if args.display:
    screen = pygame.display.set_mode(size)
i = 0
while True:
    # Output.
    if channel.get_queue() == None:
        buf = [melody.compute(x) for x in range(i, i+buffer_size)]
        i += buffer_size
        sound = pygame.sndarray.make_sound(numpy.array(buf, numpy.uint8))
        channel.queue(sound)
        if args.display:
            draw(screen, buf)

    # Control.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Common quitting methods will be caught by PyGame,
            # so do this explicitely.
            sys.exit(0)

    # Some loop breathing space.
    time.sleep(0.001)
