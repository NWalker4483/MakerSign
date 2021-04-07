from led_sign import LedSign
import pygame

FPS = 24
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = pygame.display.get_surface().get_size()
pygame.display.set_caption("MakerSign Drawing System")

clock = pygame.time.Clock()

running = True

# sign = LedSign(
#     [[10, 26, 10, 30, 27, 9, 26, 12],   # M 
#     [7, 3, 3, 3, 7, 13, 3, 6, 4, 8],    # a Wrong
#     [10, 28, 8, 12, 7, 12, 7],          # k
#     [13, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], # e
#     [12, 16, 8, 6, 5],                  # r
#     [3, 6, 3, 3, 9, 3, 4, 6, 3 ],       # S
#     [7, 15, 12, 6, 7],                  # p
#     [5, 20, 18, 7, 8],                  # a
#     [3, 3, 5, 5, 5, 5, 5, 5],           # c
#     [11, 4, 6, 7, 9, 9, 7]              # e
#     ])

# sign.save("sign.txt")

sign = LedSign.load("sign.txt")
sign.attach("/dev/cu.usbserial-1410")

sign.adjustable = True

rect = pygame.rect.Rect(0, 0, width//5, height)
rect2 = pygame.rect.Rect(width - (width//5), 0, width//5, height)
rect3 = pygame.rect.Rect(0, 0, width, height//4)
v = [20, 0]
v2 = [-20, 0]
v3 = [0, 20]
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                sign.save("sign.txt")
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                sign.clean()
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                break
    
    rect.move_ip(v)
    rect2.move_ip(v2)
    rect3.move_ip(v3)

    if rect.left < 0:
        v[0] *= -1
    if rect.right > width:
        v[0] *= -1
    if rect.top < 0:
        v[1] *= -1
    if rect.bottom > height:
        v[1] *= -1
    
    if rect2.left < 0:
        v2[0] *= -1
    if rect2.right > width:
        v2[0] *= -1
    if rect2.top < 0:
        v2[1] *= -1
    if rect2.bottom > height:
        v2[1] *= -1

    if rect3.left < 0:
        v3[0] *= -1
    if rect3.right > width:
        v3[0] *= -1
    if rect3.top < 0:
        v3[1] *= -1
    if rect3.bottom > height:
        v3[1] *= -1
    screen.fill((0, 200, 0))

    pygame.draw.rect(screen, (0,255,0), rect3)
    pygame.draw.rect(screen, (0,0,255), rect)

    pygame.draw.rect(screen, (255,0,0), rect2)

    sign.update(screen, events)
    sign.draw(screen)

    pygame.display.update()
    # - constant game speed / FPS -
    clock.tick(FPS)
