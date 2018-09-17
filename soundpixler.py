#!/usr/bin/env python3
#-*- eval: (auto-fill-mode 1); fill-column: 79; -*-
import numpy
import sys
import os
import contextlib
# Suppress pygame welcoming message, see <https://stackoverflow.com/a/51470016>.
with contextlib.redirect_stdout(None):
    import pygame


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Plom\'s glitcher')
    parser.add_argument('--frequency', dest='frequency', action='store',
                        default='8192')
    parser.add_argument('--buffer_width', dest='buffer_width', action='store',
                        default='256')
    return parser.parse_args()


def draw(screen, buf):
    background_color = (0, 0, 0)
    foreground_color = (255, 255, 255)
    lowest_line = 255
    screen.fill(background_color)
    for x, y in enumerate(buf):
        y = frame_height - y - 1
        pygame.draw.line(screen, foreground_color, (x, lowest_line), (x, y))
    pygame.display.flip()


args = parse_args()
frequency = int(args.frequency)  # samples per second
audio_bit_depth = 8  # bit size of samples
num_channels = 1  # mono
buffer_width = int(args.buffer_width)  # how many samples to buffer
pygame.mixer.pre_init(frequency, audio_bit_depth, num_channels, buffer_width)
frame_height = 2 ** audio_bit_depth

pygame.init()
channel = pygame.mixer.find_channel()
size = width, height = buffer_width, frame_height
screen = pygame.display.set_mode(size)

# large wave is one second long 
small_wave = [0] * buffer_width 
large_wave = [int(frame_height / 2)] * buffer_width # start at half max loudness
small_waves_per_large_wave = frequency / len(small_wave)

buf_edit = small_wave
clock = pygame.time.Clock()
small_wave_counter = 0
while True:

    # Output.
    if channel.get_queue() == None:
        sample_buf = []
        for pos, val in enumerate(small_wave):
            offset = small_wave_counter * len(small_wave) 
            sample_pos = offset + pos
            zoomed_out_sample_pos = int(sample_pos / small_waves_per_large_wave)
            pos_in_large_wave = zoomed_out_sample_pos % len(large_wave)
            loudness = large_wave[pos_in_large_wave] / frame_height
            sample_buf += [int(val * loudness)]
        small_wave_counter += 1
        sound = pygame.sndarray.make_sound(numpy.array(sample_buf, numpy.uint8))
        channel.queue(sound)
        draw(screen, buf_edit)

    # Control.
    pressed = pygame.mouse.get_pressed()
    if 1 in pressed:
        def draw_thicker(x, thickness):
            for i in range(0, thickness + 1):
                if x - i >= 0 and x - i < len(buf_edit):
                    buf_edit[x - i] = y
                if x + i >= 0 and x + i < len(buf_edit):
                    buf_edit[x + i] = y
        x, y = pygame.mouse.get_pos()
        y = frame_height - y - 1
        if pressed[2] == 1:
            draw_thicker(x, 4)
        elif pressed[1] == 1:
            draw_thicker(x, 1)
        elif pressed[0] == 1:
            buf_edit[x] = y
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Common quitting methods will be caught by PyGame,
            # so do this explicitely.
            sys.exit(0)
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_F1:
                buf_edit = large_wave if buf_edit == small_wave else small_wave
                    
    # Some loop breathing space.
    clock.tick(400)
