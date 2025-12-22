import math
import pygame
from pygame.locals import *
import random

# --- CONFIGURAÇÕES INICIAIS ---
pygame.init()
pygame.mixer.init()
LARGURA, ALTURA = 1366, 768
screen = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE)
clock = pygame.time.Clock()
pygame.display.set_caption("Limbus Survivors")

# --- DADOS DO PLAYER

player_hp = 10          
invulneravel = False    
timer_invulneravel = 0 
INVULNERAVEL_TEMPO = 2000  

#Caso haja erro De carregar a imagem já funciona aqui
Tamanho_mapa, Altura_mapa = 4000, 2400

# --- CARREGAMENTO DE ASSETS ---
try:
    Background_Img = pygame.image.load("LimbusSurvivors/LimbusSurvivorsIMG/Casino.png").convert()

    Tamanho_mapa = Background_Img.get_width() 
    Altura_mapa = Background_Img.get_height() 

    Jogador_Img = pygame.image.load("LimbusSurvivors/LimbusSurvivorsIMG/Ishmael_idle.png").convert_alpha()
    Jogador_Img = pygame.transform.scale(Jogador_Img, (128, 128))
    Jogador_Espelhado = pygame.transform.flip(Jogador_Img, True, False)
    
    Inimigo_Img = pygame.image.load("LimbusSurvivors/LimbusSurvivorsIMG/Middle_base.png").convert_alpha()
    Inimigo_Img = pygame.transform.scale(Inimigo_Img, (128, 128))
    
    icone = pygame.image.load("LimbusSurvivors/LimbusSurvivorsIMG/Icon.png")
    pygame.display.set_icon(icone)
    
    pygame.mixer.music.load('LimbusSurvivors/LimbusSurvivorsBGM/CasinoTheme.mp3')
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.3)

    damage_sound = pygame.mixer.Sound('LimbusSurvivors/LimbusSurvivorsBGM/IshmaelDamage.wav')
    damage_sound.set_volume(0.3)
except Exception as e:
    print(f"ERRO CRÍTICO: Arquivos não encontrados. Usando modo de depuração. Erro: {e}")
    
    Background_Img = pygame.Surface((Tamanho_mapa, Altura_mapa))
    Background_Img.fill((50, 50, 50))

    Jogador_Img = pygame.Surface((128, 128))
    Jogador_Img.fill((0, 0, 255)) 
    Jogador_Espelhado = Jogador_Img 

    Inimigo_Img = pygame.Surface((128, 128))
    Inimigo_Img.fill((255, 0, 0))

    class SomFalso:
        def play(self): pass
        def set_volume(self, v): pass
    
    damage_sound = SomFalso())

# --- VARIÁVEIS DE JOGO ---
# Mapa jogavel
Y_HORIZONTE = 960

# Player Hitbox (Menor que o sprite para ser justo)
player_rect = pygame.Rect(0, 0, 80, 80) 
player_rect.center = (Tamanho_mapa // 2, Y_HORIZONTE + (Altura_mapa - Y_HORIZONTE) // 2)

camera = pygame.Rect(0, 0, LARGURA, ALTURA)
velocidade_player = 6
espelhado = False
lista_inimigos = []
spawn_timer = 0
SPAWN_COOLDOWN = 60 
LIMITE_INIMIGOS = 15

# Constantes de Colisão
RAIO_PLAYER = 45
RAIO_INIMIGO = 35
DIST_MIN = RAIO_PLAYER + RAIO_INIMIGO

font = pygame.font.Font(None, 48)

# --- CLASSES ---
class InimigoBasico:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 60, 60)
        self.rect.center = (x, y)
        self.vel = 3
        self.hp = 10

    def atualizar(self, player_rect, inimigos):
        # 1. Direção para o jogador
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > 0:
            move_x = (dx / dist) * self.vel
            move_y = (dy / dist) * self.vel
            self.rect.x += move_x
            self.rect.y += move_y

        # 2. Separação entre inimigos (Evita tremedeira)
        for outro in inimigos:
            if outro != self:
                d_inimigo = math.hypot(self.rect.centerx - outro.rect.centerx, 
                                    self.rect.centery - outro.rect.centery)
                if 0 < d_inimigo < 60:
                    self.rect.x -= (outro.rect.centerx - self.rect.centerx) * 0.05
                    self.rect.y -= (outro.rect.centery - self.rect.centery) * 0.05

        # 3. Colisão com o Jogador (Física Circular)
        d_player = math.hypot(self.rect.centerx - player_rect.centerx, 
                            self.rect.centery - player_rect.centery)
        if 0 < d_player < DIST_MIN:
            overlap = DIST_MIN - d_player
            nx = (self.rect.centerx - player_rect.centerx) / d_player
            ny = (self.rect.centery - player_rect.centery) / d_player
            self.rect.centerx += nx * overlap
            self.rect.centery += ny * overlap

    # 4. Restrição de cenário para inimigos (para não subirem na parede)
        # O inimigo não pode passar do Y_HORIZONTE
        if self.rect.top < Y_HORIZONTE:
            self.rect.top = Y_HORIZONTE
        if self.rect.bottom > Altura_mapa:
            self.rect.bottom = Altura_mapa
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > Tamanho_mapa:
            self.rect.right = Tamanho_mapa

    def desenhar(self, surface, camera):
        # Centraliza o sprite de 128px no Rect de colisão
        pos_x = self.rect.centerx - camera.x - 64
        pos_y = self.rect.centery - camera.y - 64
        surface.blit(Inimigo_Img, (pos_x, pos_y))

# --- LOOP PRINCIPAL ---
running = True
while running:
    tempo_atual = pygame.time.get_ticks()
    # 1. ENTRADAS E EVENTOS
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
            camera.width, camera.height = event.w, event.h

    keys = pygame.key.get_pressed()
    if keys[K_ESCAPE]: running = False
    
    # Movimento do Jogador
    dx, dy = 0, 0
    if keys[K_UP]:    dy -= velocidade_player
    if keys[K_DOWN]:  dy += velocidade_player
    if keys[K_LEFT]:  dx -= velocidade_player; espelhado = True
    if keys[K_RIGHT]: dx += velocidade_player; espelhado = False

    # Normalização diagonal
    if dx != 0 and dy != 0:
        dx *= 0.707
        dy *= 0.707

    player_rect.x += dx
    player_rect.y += dy
    area_jogavel = pygame.Rect(0, Y_HORIZONTE, Tamanho_mapa, Altura_mapa - Y_HORIZONTE)
    player_rect.clamp_ip(area_jogavel)
    # 2. LÓGICA / FÍSICA
    # Spawn
    spawn_timer += 1
    if spawn_timer >= SPAWN_COOLDOWN and len(lista_inimigos) < LIMITE_INIMIGOS:
        x = random.randint(100, Tamanho_mapa - 100)
        y = random.randint(Y_HORIZONTE, Altura_mapa - 100) # Alterado aqui
        
        if math.hypot(x - player_rect.centerx, y - player_rect.centery) > 500:
            lista_inimigos.append(InimigoBasico(x, y))
            spawn_timer = 0

    # Inimigos
    for inimigo in lista_inimigos:
        inimigo.atualizar(player_rect, lista_inimigos)

    # Dano e Invulnerabilidade
    if invulneravel and tempo_atual - timer_invulneravel >= INVULNERAVEL_TEMPO:
        invulneravel = False

    for inimigo in lista_inimigos:
        if player_rect.colliderect(inimigo.rect) and not invulneravel:
            damage_sound.play()
            player_hp -= 1
            invulneravel = True
            timer_invulneravel = tempo_atual
            print(f"HP: {player_hp}")

    # Câmera segue o jogador
    camera.center = player_rect.center
    camera.clamp_ip(Rect(0, 0, Tamanho_mapa, Altura_mapa))

    # 3. RENDERIZAÇÃO
    screen.fill("black") # Fundo limpo
    
    # Desenhar Mapa
    screen.blit(Background_Img, (-camera.x, -camera.y))

    # Desenhar Inimigos
    for inimigo in lista_inimigos:
        inimigo.desenhar(screen, camera)

    # Desenhar Jogador
    desenhar_player = True
    if invulneravel:
        if (tempo_atual // 150) % 2 == 0: 
            desenhar_player = False

    if desenhar_player:
        pos_p = (player_rect.centerx - camera.x - 64, player_rect.centery - camera.y - 64)
        img = Jogador_Espelhado if espelhado else Jogador_Img
        screen.blit(img, pos_p)

    # UI
    # Inimigos
    txt = font.render(f"Inimigos: {len(lista_inimigos)}", True, "white")
    screen.blit(txt, (20, 20))
    # FPS
    fps_atual = int(clock.get_fps()) 
    txt_fps = font.render(f"FPS: {fps_atual}", True, "green") 
    screen.blit(txt_fps, (LARGURA - 150, 20))

    pygame.display.flip()

    clock.tick(60)


pygame.quit()
