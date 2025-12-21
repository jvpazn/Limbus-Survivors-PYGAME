import pygame

pygame.init()
screen = pygame.display.set_mode((1366, 768))
clock = pygame.time.Clock()
running = True


Jogador = pygame.image.load("LimbusSurvivors/LimbusSurvivorsIMG/Ishmael_idle.png")
Jogador = pygame.transform.scale(Jogador, (128, 128))
Jogador_Espelhado = pygame.transform.flip(Jogador, True, False)

icone = pygame.image.load("LimbusSurvivors/LimbusSurvivorsIMG/Icon.png")

pygame.display.set_caption("Limbus Survivors")
pygame.display.set_icon(icone)

Espelhado = False
velocidade = 6

Tamanho_mapa, Altura_mapa = 5000, 4000
mapa = pygame.Surface((Tamanho_mapa, Altura_mapa))
mapa.fill((100, 200, 100))

player_rect = Jogador.get_rect(center=(Tamanho_mapa // 2, Altura_mapa // 2))
camera = pygame.Rect(0, 0, screen.get_width(), screen.get_height())

while running:
    clock.tick(60)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player_rect.y -= velocidade
    if keys[pygame.K_DOWN]:
        player_rect.y += velocidade
    if keys[pygame.K_LEFT]:
        player_rect.x -= velocidade
        Espelhado = True
    if keys[pygame.K_RIGHT]:
        player_rect.x += velocidade
        Espelhado = False

    if keys[pygame.K_ESCAPE]:
        running = False

    camera.center = player_rect.center

    camera.clamp_ip(pygame.Rect(0, 0, Tamanho_mapa, Altura_mapa))


    screen.fill("black")
    screen.blit(mapa, (-camera.x, -camera.y))  

    if Espelhado:
        screen.blit(Jogador_Espelhado, (player_rect.x - camera.x, player_rect.y - camera.y))
    else:
        screen.blit(Jogador, (player_rect.x - camera.x, player_rect.y - camera.y))

    pygame.display.update()

pygame.quit()