import math
import pygame
from pygame.locals import *
import random
import os

# --- CONFIGURAÇÕES INICIAIS ---
pygame.init()
pygame.mixer.init()

# Variáveis Globais de Janela
LARGURA, ALTURA = 1366, 768
screen = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE)
clock = pygame.time.Clock()
pygame.display.set_caption("Limbus Survivors Beta")

# Valores padrão de mapa (evitar bugs)
Tamanho_mapa, Altura_mapa = 4000, 2400

# --- PREPARAÇÃO DE DIRETÓRIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "LimbusSurvivorsIMG")
BGM_DIR = os.path.join(BASE_DIR, "LimbusSurvivorsBGM")

print(f"Diretório Base: {BASE_DIR}")

# --- FUNÇÕES DE CARREGAMENTO ---
def img(nome):
    path = os.path.join(IMG_DIR, nome)
    if not os.path.exists(path):
        return None 
    return pygame.image.load(path).convert_alpha()

def music(nome):
    path = os.path.join(BGM_DIR, nome)
    if os.path.exists(path):
        pygame.mixer.music.load(path)

def sfx(nome, volume=1.0):
    path = os.path.join(BGM_DIR, nome)
    if os.path.exists(path):
        som = pygame.mixer.Sound(path)
        som.set_volume(volume)
        return som
    return None

def carregar_spritesheet_grade(nome_arquivo, colunas, linhas, escala_final=None):
    sheet = img(nome_arquivo)
    if not sheet:
        return []

    w_total = sheet.get_width()
    h_total = sheet.get_height()

    largura_frame = w_total // colunas
    altura_frame = h_total // linhas

    frames = []

    for linha in range(linhas):
        for coluna in range(colunas):
            rect = pygame.Rect(
                coluna * largura_frame,
                linha * altura_frame,
                largura_frame,
                altura_frame
            )
            frame = sheet.subsurface(rect)
            if escala_final:
                frame = pygame.transform.scale(frame, escala_final)
            frames.append(frame)

    return frames

# --- CARREGAMENTO DE ASSETS ---
try:
    #Fundo
    tmp_bg = img("Casino.png")
    if tmp_bg:
        Background_Img = tmp_bg
        Tamanho_mapa = Background_Img.get_width() 
        Altura_mapa = Background_Img.get_height() 
    else:
        Background_Img = pygame.Surface((Tamanho_mapa, Altura_mapa))
        Background_Img.fill((50, 50, 50))

    #Jogador
    tmp_player = img("Ishmael_idle.png") 
    if tmp_player:
        Jogador_Img = pygame.transform.scale(tmp_player, (128, 128))
    else:
        Jogador_Img = pygame.Surface((128, 128))
        Jogador_Img.fill((0, 255, 0)) # Quadrado Verde
    
    Jogador_Espelhado = pygame.transform.flip(Jogador_Img, True, False)
    
    #Ícone UI
    Icone_Jogador = img("Ishmael_Icon.png")
    if not Icone_Jogador:
        Icone_Jogador = pygame.Surface((40, 40))
        Icone_Jogador.fill((0, 0, 255))

    #Inimigo
    Inimigo_Img = img("Middle_base.png")
    if not Inimigo_Img:
        Inimigo_Img = pygame.Surface((128, 128))
        Inimigo_Img.fill((255, 0, 0)) 
    else:
        Inimigo_Img = pygame.transform.scale(Inimigo_Img, (128, 128))

    #Arma
    Arma_Img = img("IshmaelWeapon.png")
    COMPRIMENTO_ARMA = 100 
    LARGURA_ARMA = 100 

    if not Arma_Img:
        Arma_Img = pygame.Surface((COMPRIMENTO_ARMA, LARGURA_ARMA))
        Arma_Img.fill((0, 200, 255)) 
        pygame.draw.rect(Arma_Img, (255,0,0), (COMPRIMENTO_ARMA-10, 0, 10, LARGURA_ARMA))
    else:
        Arma_Img = pygame.transform.scale(Arma_Img, (LARGURA_ARMA, COMPRIMENTO_ARMA))
        Arma_Img = pygame.transform.rotate(Arma_Img, 90)

    #Explosão
    frames_explosao = carregar_spritesheet_grade("IshExplosion.png", 2, 3, (150, 150))
    if frames_explosao:
        animacao_explosao = frames_explosao
    else:
        animacao_explosao = []
        for i in range(6):
            fallback = pygame.Surface((150, 150), pygame.SRCALPHA)
            raio = 10 + (i * 20)
            pygame.draw.circle(fallback, (255, 100, 0, 200), (80, 80), raio)
            animacao_explosao.append(fallback)

    #Sons
    img_icone = img("Icon.png")
    if img_icone: pygame.display.set_icon(img_icone)
    
    music("CasinoTheme.mp3")
    if pygame.mixer.music.get_busy() == False and os.path.exists(os.path.join(BGM_DIR, "CasinoTheme.mp3")):
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0)

    damage_sound = sfx("IshmaelDamage.wav", 0.3)
    explosao_sound = sfx("Explosion.wav", 0.4) 

except Exception as e:
    print(f"ERRO NOS ASSETS: {e}")

# --- VARIÁVEIS DE JOGO ---
Y_HORIZONTE = 960

player_rect = pygame.Rect(0, 0, 80, 80) 
player_rect.center = (Tamanho_mapa // 2, Y_HORIZONTE + (Altura_mapa - Y_HORIZONTE) // 2)

camera = pygame.Rect(0, 0, LARGURA, ALTURA)
lista_inimigos = []
lista_explosoes = [] 

spawn_timer = 0
SPAWN_COOLDOWN = 180 
LIMITE_INIMIGOS = 15

# Status Player
playerMax_hp = 10
player_hp = 10          
invulneravel = False    
timer_invulneravel = 0 
INVULNERAVEL_TEMPOBase = 1500  
INVULNERAVEL_TEMPO = 1500  
velocidade_playerBase = 6
velocidade_player = 6
danoBase = 3
dano = 3
COOLDOWN_ARMA_BASE = 1500
COOLDOWN_ARMA = 1500
ultimo_ataque = 0 
espelhado = False 
Level = 1
xp = 0
xp_passar_nivel = 130

def passar_nivel(LevelAtual, xpNivel, xpAtual):
    while xpAtual >= xpNivel:
        LevelAtual += 1
        xpAtual = xpAtual - xpNivel
        xpNivel = int(xpNivel * 1.15)
    else:
        pass
    return LevelAtual, xpNivel, xpAtual


# E.G.O Gifts

grade_fixerHaving = False
# Se grade_fixerHaving For TRUE automaticamente grade_fixerLevel tem que ser 1 ou mais
grade_fixerLevel = 0

def GradeFixerEGO(Having, level):
    global dano, COOLDOWN_ARMA, velocidade_player, INVULNERAVEL_TEMPO
    if Having == True:
        if level == 1:
            dano = danoBase * 1.02
            COOLDOWN_ARMA = COOLDOWN_ARMA_BASE * 0.98
            velocidade_player = velocidade_playerBase * 1.02
            INVULNERAVEL_TEMPO = INVULNERAVEL_TEMPOBase * 1.02
        if level == 2:
            dano = danoBase * 1.05
            COOLDOWN_ARMA = COOLDOWN_ARMA_BASE * 0.95
            velocidade_player = velocidade_playerBase * 1.05
            INVULNERAVEL_TEMPO = INVULNERAVEL_TEMPOBase * 1.05
        if level == 3:
            dano = danoBase * 1.07
            COOLDOWN_ARMA = COOLDOWN_ARMA_BASE * 0.93
            velocidade_player = velocidade_playerBase * 1.07
            INVULNERAVEL_TEMPO = INVULNERAVEL_TEMPOBase * 1.07
        if level == 4:
            dano = danoBase * 1.10
            COOLDOWN_ARMA = COOLDOWN_ARMA_BASE * 0.90
            velocidade_player = velocidade_playerBase * 1.10
            INVULNERAVEL_TEMPO = INVULNERAVEL_TEMPOBase * 1.10
        if level == 5:
            dano = danoBase * 1.15
            COOLDOWN_ARMA = COOLDOWN_ARMA_BASE * 0.85
            velocidade_player = velocidade_playerBase * 1.15
            INVULNERAVEL_TEMPO = INVULNERAVEL_TEMPOBase * 1.15
    else:
        pass


# Cores
VERMELHO = (220, 20, 60) 
CINZA_ESCURO = (50, 50, 50)
CINZA_CLARO = (100, 100, 100)
BRANCO = (255, 255, 255)
CIANO = (0, 255, 255) # Cor da barra de recarga

# --- CLASSES ---
class Explosao(pygame.sprite.Sprite):
    def __init__(self, x, y, frames):
        pygame.sprite.Sprite.__init__(self)
        self.frames = frames
        self.frame_atual = 0
        self.image = self.frames[self.frame_atual]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 60 
        self.atingidos = [] 

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame_atual += 1
            if self.frame_atual == len(self.frames):
                return False 
            else:
                self.image = self.frames[self.frame_atual]
        return True 

    def desenhar(self, surface, camera):
        pos_x = self.rect.centerx - camera.x - (self.rect.width // 2)
        pos_y = self.rect.centery - camera.y - (self.rect.height // 2)
        surface.blit(self.image, (pos_x, pos_y))

class InimigoBasico:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 60, 60)
        self.rect.center = (x, y)
        self.vel = 3
        self.max_hp = 10 # Salvei o maximo pra calcular a barra
        self.hp = self.max_hp 
        self.kb_x = 0
        self.kb_y = 0
        self.atrito = 0.9
        self.xp_drop = 15

    def atualizar(self, player_rect, inimigos):
# Movimento Normal ---
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        move_x = 0
        move_y = 0
        forca_kb = math.hypot(self.kb_x, self.kb_y)
        
        if dist > 0 and forca_kb < 10: 
            move_x = (dx / dist) * self.vel
            move_y = (dy / dist) * self.vel

        #Knockback ---
        self.rect.x += move_x + self.kb_x
        self.rect.y += move_y + self.kb_y

        # Reduz o knockback
        self.kb_x *= self.atrito
        self.kb_y *= self.atrito

        # Limpa valores muito pequenos para parar processamento desnecessário
        if abs(self.kb_x) < 0.1: self.kb_x = 0
        if abs(self.kb_y) < 0.1: self.kb_y = 0

        #Empurrão
        for outro in inimigos:
            if outro != self:
                if self.rect.colliderect(outro.rect):
                    if self.rect.centerx < outro.rect.centerx: self.rect.x -= 1
                    else: self.rect.x += 1
                    if self.rect.centery < outro.rect.centery: self.rect.y -= 1
                    else: self.rect.y += 1

        #Colisão Player
        d_player = math.hypot(self.rect.centerx - player_rect.centerx, 
                            self.rect.centery - player_rect.centery)
        if 0 < d_player < DIST_MIN:
            overlap = DIST_MIN - d_player
            nx = (self.rect.centerx - player_rect.centerx) / d_player
            ny = (self.rect.centery - player_rect.centery) / d_player
            self.rect.centerx += nx * overlap
            self.rect.centery += ny * overlap

        #Limites
        if self.rect.top < Y_HORIZONTE: self.rect.top = Y_HORIZONTE
        if self.rect.bottom > Altura_mapa: self.rect.bottom = Altura_mapa
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > Tamanho_mapa: self.rect.right = Tamanho_mapa

    def desenhar(self, surface, camera):
        # Desenha a imagem do inimigo
        pos_x = self.rect.centerx - camera.x - 64
        pos_y = self.rect.centery - camera.y - 64
        surface.blit(Inimigo_Img, (pos_x, pos_y))
        
        # --- DESENHO DA BARRA DE VIDA DO INIMIGO ---
        if self.hp < self.max_hp: # Só desenha se tomou dano
            largura_barra = 60
            altura_barra = 5
            padding_y = 10 # Distância acima da cabeça
            
            pos_barra_x = self.rect.centerx - camera.x - (largura_barra // 2)
            pos_barra_y = self.rect.top - camera.y - padding_y
            
            # Fundo da barra
            pygame.draw.rect(surface, CINZA_ESCURO, (pos_barra_x, pos_barra_y, largura_barra, altura_barra))
            
            # Vida atual
            porcentagem_vida = self.hp / self.max_hp
            largura_atual = int(largura_barra * porcentagem_vida)
            if largura_atual > 0:
                pygame.draw.rect(surface, VERMELHO, (pos_barra_x, pos_barra_y, largura_atual, altura_barra))

# --- UI ---
def desenhar_vida(superficie, x, y, vida_atual, vida_maxima, icone):
    tamanho_quadrado = 20
    tamanho_icone = 40
    padding = 10
    
    icone_scale = pygame.transform.scale(icone, (tamanho_icone, tamanho_icone))
    offset_y_barra = (tamanho_icone - tamanho_quadrado) // 2
    
    superficie.blit(icone_scale, (x, y))

    inicio_barra_x = x + tamanho_icone + padding
    pos_y_barra = y + offset_y_barra

    for i in range(vida_maxima):
        pos_x = inicio_barra_x + (tamanho_quadrado) * i
        rect = (pos_x, pos_y_barra, tamanho_quadrado, tamanho_quadrado)
        if i < vida_atual:
            pygame.draw.rect(superficie, VERMELHO, rect) 
        else:
            pygame.draw.rect(superficie, CINZA_ESCURO, rect) 

    largura_total = (tamanho_quadrado * vida_maxima)
    rect_borda = (inicio_barra_x, pos_y_barra, largura_total, tamanho_quadrado)
    pygame.draw.rect(superficie, BRANCO, rect_borda, 2)

# Constantes de Colisão
RAIO_PLAYER = 45
RAIO_INIMIGO = 35
DIST_MIN = RAIO_PLAYER + RAIO_INIMIGO

font = pygame.font.Font(None, 48)

# --- LOOP PRINCIPAL ---
running = True
while running:
    tempo_atual = pygame.time.get_ticks()

    # --- CÁLCULO DE VETORES ---
    mx, my = pygame.mouse.get_pos()
    mouse_mundo_x = mx + camera.x
    mouse_mundo_y = my + camera.y

    vetor_x = mouse_mundo_x - player_rect.centerx
    vetor_y = mouse_mundo_y - player_rect.centery

    angulo_radianos = math.atan2(-vetor_y, vetor_x) 
    angulo_graus = math.degrees(angulo_radianos)

    if vetor_x < 0:
        espelhado = True
    else:
        espelhado = False

    # --- EVENTOS ---
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == VIDEORESIZE:
            LARGURA, ALTURA = event.w, event.h
            screen = pygame.display.set_mode((LARGURA, ALTURA), RESIZABLE)
            camera.width, camera.height = LARGURA, ALTURA
        
        # --- SISTEMA DE COMBATE (CLIQUE COM TIMER) ---
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1: # Botão Esquerdo
                
                agora = pygame.time.get_ticks()
                if agora - ultimo_ataque >= COOLDOWN_ARMA:
                    
                    ultimo_ataque = agora 
                    
                    # Calcular onde a ponta da arma está no mundo
                    distancia_explosao = COMPRIMENTO_ARMA 
                    
                    ponta_arma_x = player_rect.centerx + (math.cos(angulo_radianos) * distancia_explosao)
                    ponta_arma_y = player_rect.centery - (math.sin(angulo_radianos) * distancia_explosao)
                    
                    # Instancia a explosão na PONTA DA ARMA
                    nova_explosao = Explosao(ponta_arma_x, ponta_arma_y, animacao_explosao)
                    lista_explosoes.append(nova_explosao)
                    
                    if explosao_sound:
                        explosao_sound.play()


    keys = pygame.key.get_pressed()
    if keys[K_ESCAPE]: running = False
    
    #Movimento Jogador
    dx, dy = 0, 0
    if keys[K_UP] or keys[K_w]:    dy -= velocidade_player
    if keys[K_DOWN] or keys[K_s]:  dy += velocidade_player
    if keys[K_LEFT] or keys[K_a]:  dx -= velocidade_player
    if keys[K_RIGHT] or keys[K_d]: dx += velocidade_player


    if dx != 0 and dy != 0:
        dx *= 0.707
        dy *= 0.707

    player_rect.x += dx
    player_rect.y += dy
    area_jogavel = pygame.Rect(0, Y_HORIZONTE, Tamanho_mapa, Altura_mapa - Y_HORIZONTE)
    player_rect.clamp_ip(area_jogavel)

    # Spawns
    spawn_timer += 1
    if spawn_timer >= SPAWN_COOLDOWN and len(lista_inimigos) < LIMITE_INIMIGOS:
        x = random.randint(100, Tamanho_mapa - 100)
        y = random.randint(Y_HORIZONTE, Altura_mapa - 100)
        if math.hypot(x - player_rect.centerx, y - player_rect.centery) > 500:
            lista_inimigos.append(InimigoBasico(x, y))
            spawn_timer = 0

    # Atualizações
    for inimigo in lista_inimigos:
        inimigo.atualizar(player_rect, lista_inimigos)

    # Lógica da Explosão (Dano/Knockback)
    for explosao in lista_explosoes[:]:
        ativa = explosao.update()
        if not ativa:
            lista_explosoes.remove(explosao)
        else:
            # Usamos uma cópia da lista [:] para poder remover inimigos sem bugar o loop
            for inimigo in lista_inimigos[:]:
                if explosao.rect.colliderect(inimigo.rect):
                    if inimigo not in explosao.atingidos:
                        if inimigo not in explosao.atingidos:
                        
                            # CÁLCULO DO VETOR
                            dx = inimigo.rect.centerx - explosao.rect.centerx
                            dy = inimigo.rect.centery - explosao.rect.centery
                            dist = math.hypot(dx, dy)
                            
                            if dist > 0:

                                impulso = 12
                                
                                inimigo.kb_x = (dx / dist) * impulso
                                inimigo.kb_y = (dy / dist) * impulso

                    # 2. DANO - Acontece apenas SE o inimigo ainda não foi atingido por ESSA explosão
                    if inimigo not in explosao.atingidos:
                        inimigo.hp -= dano          
                        explosao.atingidos.append(inimigo) 
                        
                        # 3. MORTE
                        if inimigo.hp <= 0:
                            if inimigo in lista_inimigos:
                                lista_inimigos.remove(inimigo)
                                xp += inimigo.xp_drop

    # Colisão Inimigo -> Player
    if invulneravel and tempo_atual - timer_invulneravel >= INVULNERAVEL_TEMPO:
        invulneravel = False

    for inimigo in lista_inimigos:
        dx = player_rect.centerx - inimigo.rect.centerx
        dy = player_rect.centery - inimigo.rect.centery
        distancia = math.hypot(dx, dy)
        
        if distancia < (DIST_MIN + 5) and not invulneravel:
            if damage_sound: damage_sound.play()
            player_hp -= 1
            invulneravel = True
            timer_invulneravel = tempo_atual
            
    if player_hp <= 0:
        print("Game Over")
        running = False 

    #Upar de nivel, etc
    Level, xp_passar_nivel, xp = passar_nivel(Level, xp_passar_nivel, xp)
    GradeFixerEGO(grade_fixerHaving, grade_fixerLevel)

    # Câmera
    camera.center = player_rect.center
    camera.clamp_ip(Rect(0, 0, Tamanho_mapa, Altura_mapa))

    # --- RENDERIZAÇÃO ---
    screen.fill("black") 
    screen.blit(Background_Img, (-camera.x, -camera.y))

    # Desenha Explosões (Camada inferior)
    for explosao in lista_explosoes:
        explosao.desenhar(screen, camera)

    # Desenha Inimigos (e suas barras de vida)
    for inimigo in lista_inimigos:
        inimigo.desenhar(screen, camera)

    # Desenha Jogador + Arma
    desenhar_player = True
    if invulneravel and (tempo_atual // 150) % 2 == 0: 
        desenhar_player = False

    if desenhar_player:
        pos_p_x = player_rect.centerx - camera.x - 64
        pos_p_y = player_rect.centery - camera.y - 64
        
        img_p = Jogador_Espelhado if espelhado else Jogador_Img
        screen.blit(img_p, (pos_p_x, pos_p_y))
        
        # --- DESENHO DA BARRA DE RECARGA (COOLDOWN) ---
        tempo_passado = tempo_atual - ultimo_ataque
        if tempo_passado < COOLDOWN_ARMA:
            porcentagem = tempo_passado / COOLDOWN_ARMA
            
            largura_barra = 60
            altura_barra = 6
            padding_y = 15 
            
            # Posição centrada acima do player
            pos_barra_x = player_rect.centerx - camera.x - (largura_barra // 2)
            pos_barra_y = player_rect.top - camera.y - padding_y
            
            # Fundo Cinza Claro
            pygame.draw.rect(screen, CINZA_CLARO, (pos_barra_x, pos_barra_y, largura_barra, altura_barra))
            
            # Progresso Ciano
            largura_atual = int(largura_barra * porcentagem)
            if largura_atual > 0:
                pygame.draw.rect(screen, BRANCO, (pos_barra_x, pos_barra_y, largura_atual, altura_barra))

        # --- DESENHO DA ARMA ROTACIONADA ---
        arma_rotacionada = pygame.transform.rotate(Arma_Img, angulo_graus)
        rect_arma = arma_rotacionada.get_rect()

        # Define o "offset" (distância do centro da arma até o player)
        distancia_do_cabo_ao_centro = Arma_Img.get_width() / 2 
        
        offset_x = math.cos(angulo_radianos) * distancia_do_cabo_ao_centro
        offset_y = -math.sin(angulo_radianos) * distancia_do_cabo_ao_centro

        # Posiciona o rect da arma
        rect_arma.centerx = player_rect.centerx + offset_x 
        rect_arma.centery = player_rect.centery + offset_y

        # Desenha na tela (compensando a câmera)
        screen.blit(arma_rotacionada, (rect_arma.x - camera.x, rect_arma.y - camera.y))

    # UI
    desenhar_vida(screen, 20, 20, player_hp, playerMax_hp, Icone_Jogador)

    txt = font.render(f"Inimigos: {len(lista_inimigos)}", True, "white")
    txt_rect = txt.get_rect(center=(LARGURA // 2, 30))
    screen.blit(txt, txt_rect)
    
    txt_lvl = font.render(f"LVL: {Level} | XP: {int(xp)}/{xp_passar_nivel}", True, "yellow")
    screen.blit(txt_lvl, (20, 80))

    fps_atual = int(clock.get_fps()) 
    txt_fps = font.render(f"FPS: {fps_atual}", True, "green") 
    screen.blit(txt_fps, (LARGURA - 150, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
