def process_input(input_queue, screen):
    while True:
        keypress = screen.getkey()
        input_queue.put(keypress)
