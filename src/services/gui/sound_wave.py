"""
Componente de visualização de ondas sonoras para feedback visual.
"""
import math
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QWidget


class SoundWaveVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 80)
        
        # Estado da visualização
        self._active = False
        self._speaking = False
        self._listening = False
        self._idle = True
        
        # Configurações de animação
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  # 20 FPS
        
        # Dados da animação
        self.wave_points = []
        self.amplitude = 0
        self.phase = 0
        self.target_amplitude = 0
        self.color = QColor(0, 120, 215)  # Cor azul padrão
        
        # Configurar aparência
        self.setAutoFillBackground(False)
        self.update_animation()
    
    def set_idle(self):
        """Define o estado como ocioso."""
        self._idle = True
        self._listening = False
        self._speaking = False
        self.target_amplitude = 5
        self.color = QColor(180, 180, 180)  # Cinza
    
    def set_listening(self):
        """Define o estado como escutando."""
        self._idle = False
        self._listening = True
        self._speaking = False
        self.target_amplitude = 20
        self.color = QColor(0, 120, 215)  # Azul
    
    def set_speaking(self):
        """Define o estado como falando."""
        self._idle = False
        self._listening = False
        self._speaking = True
        self.target_amplitude = 30
        self.color = QColor(0, 170, 120)  # Verde
    
    def set_active(self, active):
        """Define se a visualização está ativa."""
        self._active = active
        if not active:
            self.set_idle()
    
    def update_animation(self):
        """Atualiza os dados da animação."""
        # Atualiza a amplitude suavemente
        if self.amplitude < self.target_amplitude:
            self.amplitude = min(self.target_amplitude, self.amplitude + 2)
        elif self.amplitude > self.target_amplitude:
            self.amplitude = max(self.target_amplitude, self.amplitude - 2)
        
        # Atualiza a fase
        self.phase += 0.2
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi
        
        # Gera os pontos da onda
        self.generate_wave_points()
        
        self.update()
    
    def generate_wave_points(self):
        """Gera os pontos para desenhar a onda sonora."""
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Limpa os pontos anteriores
        self.wave_points = []
        
        # Gera pontos para uma onda senoidal com ruído
        if self._idle:
            # Modo ocioso: ondas pequenas e suaves
            for x in range(width):
                t = x / width * 4 * math.pi + self.phase
                y = center_y + math.sin(t) * self.amplitude * 0.5
                self.wave_points.append((x, y))
        elif self._listening:
            # Modo de escuta: ondas responsivas
            for x in range(width):
                t = x / width * 6 * math.pi + self.phase
                noise = np.random.normal(0, 1) * 2  # Ruído aleatório pequeno
                y = center_y + math.sin(t) * self.amplitude + noise
                self.wave_points.append((x, y))
        elif self._speaking:
            # Modo falando: ondas mais intensas e complexas
            for x in range(width):
                t = x / width * 8 * math.pi + self.phase
                noise = np.random.normal(0, 1) * 3  # Ruído aleatório maior
                y = center_y + math.sin(t) * self.amplitude + math.sin(t * 2) * self.amplitude * 0.5 + noise
                self.wave_points.append((x, y))
    
    def paintEvent(self, event):
        """Desenha a visualização da onda sonora."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Configura a caneta
        pen = QPen(self.color)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Cria e desenha o caminho da onda
        if self.wave_points:
            path = QPainterPath()
            path.moveTo(self.wave_points[0][0], self.wave_points[0][1])
            
            for i in range(1, len(self.wave_points)):
                path.lineTo(self.wave_points[i][0], self.wave_points[i][1])
            
            painter.drawPath(path)
