"""
Interface gráfica principal da aplicação.
"""
import os
import sys
import threading
import time
from enum import Enum

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QSystemTrayIcon, QMenu,
    QDialog, QTextEdit, QScrollArea, QFrame, QStyle
)

import qdarkstyle
import pyqtgraph as pg
from .sound_wave import SoundWaveVisualizer
from ..tuya_api import get_tuya_devices


class AssistantState(Enum):
    """Estados possíveis do assistente."""
    IDLE = 0
    LISTENING = 1
    PROCESSING = 2
    SPEAKING = 3


class MessageType(Enum):
    """Tipos de mensagens no histórico."""
    USER = 0
    ASSISTANT = 1
    SYSTEM = 2


class ConversationWidget(QWidget):
    """Widget para exibir o histórico de conversas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Área de rolagem para as mensagens
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #222222;
                border-radius: 8px;
                border: 1px solid #333333;
            }
        """)
        
        # Widget para conter as mensagens
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(15)  # Aumentando o espaçamento entre mensagens
        self.messages_layout.addStretch()
        self.messages_widget.setLayout(self.messages_layout)
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Adiciona uma barra de status com timestamp
        self.timestamp_label = QLabel("Iniciado em: " + time.strftime("%H:%M:%S"))
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.timestamp_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.timestamp_label)
        
        # Timer para rolar para a mensagem mais recente
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.scroll_to_bottom)
        self.scroll_timer.setInterval(100)
    
    def scroll_to_bottom(self):
        """Rola para a última mensagem."""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    def add_message(self, text, message_type):
        """Adiciona uma mensagem ao histórico."""
        message_widget = QWidget()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(5, 5, 5, 5)
        
        # Adiciona timestamp à mensagem
        timestamp = time.strftime("%H:%M:%S")
        
        # Cria o widget de texto da mensagem
        message_text = QTextEdit()
        message_text.setReadOnly(True)
        
        # Formata o texto com timestamp
        formatted_text = f"<span style='color: #888888; font-size: 10px;'>[{timestamp}]</span><br>{text}"
        message_text.setHtml(formatted_text)
        message_text.setMinimumHeight(50)
        message_text.setMaximumHeight(150)
        
        # Configura o estilo com base no tipo de mensagem
        if message_type == MessageType.USER:
            message_text.setStyleSheet("""
                QTextEdit {
                    background-color: #2A82DA;
                    border-radius: 10px;
                    padding: 8px;
                    color: white;
                    border: 1px solid #1A72CA;
                }
            """)
            message_layout.addStretch()
            message_layout.addWidget(message_text)
        elif message_type == MessageType.ASSISTANT:
            message_text.setStyleSheet("""
                QTextEdit {
                    background-color: #333333;
                    border-radius: 10px;
                    padding: 8px;
                    color: white;
                    border: 1px solid #444444;
                }
            """)
            message_layout.addWidget(message_text)
            message_layout.addStretch()
        else:  # SYSTEM
            message_text.setStyleSheet("""
                QTextEdit {
                    background-color: #444444;
                    border-radius: 10px;
                    padding: 8px;
                    color: #CCCCCC;
                    font-style: italic;
                    border: 1px solid #555555;
                }
            """)
            message_layout.addStretch(1)
            message_layout.addWidget(message_text)
            message_layout.addStretch(1)
        
        message_widget.setLayout(message_layout)
        
        # Adiciona a mensagem antes do último stretch
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)
        
        # Atualiza o timestamp
        self.timestamp_label.setText("Última atualização: " + timestamp)
        
        # Agenda rolagem para a última mensagem
        self.scroll_timer.start()


class AssistantThread(QThread):
    """Thread para executar o assistente em segundo plano."""
    state_changed = pyqtSignal(AssistantState)
    message_received = pyqtSignal(str, MessageType)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.paused = False
        self.devices = []
        self.openapi = None
    
    def run(self):
        """Executa o assistente em segundo plano."""
        import main
        
        self.running = True
        self.message_received.emit("Assistente iniciado.", MessageType.SYSTEM)
        
        # Obtém os dispositivos Tuya (poderá ser alterado para usar as credenciais salvas)
        try:
            self.openapi, self.devices = get_tuya_devices()
            device_count = len(self.devices)
            if device_count > 0:
                self.message_received.emit(f"Conectado a {device_count} dispositivos Tuya.", MessageType.SYSTEM)
            else:
                self.message_received.emit("Nenhum dispositivo Tuya encontrado.", MessageType.SYSTEM)
        except Exception as e:
            self.message_received.emit(f"Erro ao conectar aos dispositivos Tuya: {str(e)}", MessageType.SYSTEM)
        
        # Inicia o assistente
        self.state_changed.emit(AssistantState.IDLE)
        self.message_received.emit("Assistente pronto. Diga 'Alexa' para começar.", MessageType.SYSTEM)
        
        # Monkey patch para interceptar os comandos e atualizar a UI
        original_falar = main.falar.falar
        
        def falar_intercept(texto):
            self.state_changed.emit(AssistantState.SPEAKING)
            self.message_received.emit(texto, MessageType.ASSISTANT)
            result = original_falar(texto)
            self.state_changed.emit(AssistantState.IDLE)
            return result
        
        main.falar.falar = falar_intercept
        
        # Monkey patch para interceptar o reconhecimento de voz
        original_wake_word_listener = main.wake_word_listener
        
        def wake_word_listener_intercept(openapi, devices):
            self.state_changed.emit(AssistantState.IDLE)
            
            import pvporcupine
            import pyaudio
            import speech_recognition as sr
            
            porcupine = pvporcupine.create(
                access_key="fOnTL0b3dkpAXakuPhoncWUi/cehGu7KoXuctpYNuHMwrgShm5WUWg==",
                keywords=["alexa"],
            )

            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
            )

            recognizer = sr.Recognizer()
            mic = sr.Microphone()
            
            try:
                while self.running and not self.paused:
                    pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                    pcm_unpacked = memoryview(pcm).cast('h')
                    keyword_index = porcupine.process(pcm_unpacked)

                    if keyword_index >= 0:
                        self.state_changed.emit(AssistantState.LISTENING)
                        self.message_received.emit("Palavra-chave detectada. Ouvindo comando...", MessageType.SYSTEM)

                        with mic as source:
                            try:
                                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
                                texto = recognizer.recognize_google(audio, language="pt-BR").lower()

                                if texto.startswith("alexa"):
                                    texto = texto.replace("alexa", "", 1).strip()

                                self.message_received.emit(texto, MessageType.USER)
                                self.state_changed.emit(AssistantState.PROCESSING)

                                if texto == "sair":
                                    main.falar.falar("Encerrando assistente. Até logo!")
                                    self.running = False
                                    break

                                main.executar_comando(texto, openapi, devices)

                            except sr.WaitTimeoutError:
                                self.message_received.emit("Você não falou nada após a palavra-chave.", MessageType.SYSTEM)
                                main.falar.falar("Não ouvi nada. Pode tentar novamente.")
                            except sr.UnknownValueError:
                                self.message_received.emit("Não entendi o comando.", MessageType.SYSTEM)
                                main.falar.falar("Desculpe, não entendi.")
                            except sr.RequestError as e:
                                self.message_received.emit(f"Erro ao conectar com API de voz: {e}", MessageType.SYSTEM)
                                main.falar.falar("Erro ao conectar com o serviço de voz.")
                            
                            self.state_changed.emit(AssistantState.IDLE)
            finally:
                stream.stop_stream()
                stream.close()
                pa.terminate()
                porcupine.delete()
                self.state_changed.emit(AssistantState.IDLE)
        
        main.wake_word_listener = wake_word_listener_intercept
        
        # Inicia o assistente
        if self.openapi and self.devices:
            main.wake_word_listener(self.openapi, self.devices)
    
    def stop(self):
        """Para o assistente."""
        self.running = False
    
    def pause(self):
        """Pausa o assistente."""
        self.paused = True
    
    def resume(self):
        """Retoma o assistente."""
        self.paused = False


class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    def __init__(self):
        super().__init__()
        
        self.setup_ui()
        self.setup_tray_icon()
        
        # Inicializa o assistente
        self.assistant_thread = AssistantThread()
        self.assistant_thread.state_changed.connect(self.on_assistant_state_changed)
        self.assistant_thread.message_received.connect(self.on_message_received)
        self.assistant_thread.start()
    
    def setup_ui(self):
        """Configura a interface do usuário."""
        self.setWindowTitle("Assistente Virtual")
        self.setMinimumSize(800, 600)  # Aumentando o tamanho da janela
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Título
        title_layout = QHBoxLayout()
        
        # Tenta carregar o ícone do arquivo ou usa um ícone padrão
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
        else:
            # Cria um pixmap vazio como fallback
            pixmap = QPixmap(48, 48)
            pixmap.fill(Qt.GlobalColor.transparent)
            
        icon_label = QLabel()
        icon_label.setPixmap(pixmap.scaled(QSize(48, 48), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("Assistente Virtual")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Layout principal dividido em duas partes
        content_layout = QHBoxLayout()
        
        # Parte esquerda - visualizador de ondas e status
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Visualizador de ondas sonoras
        self.wave_visualizer = SoundWaveVisualizer()
        left_layout.addWidget(self.wave_visualizer, 2)
        
        # Status do assistente
        status_widget = QWidget()
        status_layout = QVBoxLayout()
        status_widget.setLayout(status_layout)
        
        self.status_label = QLabel("Aguardando comando...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 14))
        status_layout.addWidget(self.status_label)
        
        # Instruções
        instructions_label = QLabel("Diga 'Alexa' para ativar o assistente")
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setStyleSheet("color: #999999; font-style: italic;")
        status_layout.addWidget(instructions_label)
        
        left_layout.addWidget(status_widget)
        
        # Parte direita - histórico de conversas
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Título do histórico
        log_title = QLabel("Histórico de Interações")
        log_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        log_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(log_title)
        
        # Histórico de conversas
        self.conversation_widget = ConversationWidget()
        right_layout.addWidget(self.conversation_widget, 1)
        
        # Adiciona os painéis ao layout principal
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel, 2)  # Dá mais espaço para o histórico
        
        main_layout.addLayout(content_layout, 1)
    
    def setup_tray_icon(self):
        """Configura o ícone da bandeja do sistema."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Tenta carregar o ícone do arquivo ou usa um ícone padrão
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Usa um ícone padrão do sistema como fallback
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        
        restore_action = QAction("Mostrar Assistente", self)
        restore_action.triggered.connect(self.showNormal)
        tray_menu.addAction(restore_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """Manipula a ativação do ícone da bandeja."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
    
    def closeEvent(self, event):
        """Manipula o evento de fechar a janela."""
        # Pergunta ao usuário se deseja fechar ou minimizar para a bandeja
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    @pyqtSlot(AssistantState)
    def on_assistant_state_changed(self, state):
        """Manipula a mudança de estado do assistente."""
        if state == AssistantState.IDLE:
            self.status_label.setText("Aguardando comando...")
            self.wave_visualizer.set_idle()
        elif state == AssistantState.LISTENING:
            self.status_label.setText("Ouvindo...")
            self.wave_visualizer.set_listening()
        elif state == AssistantState.PROCESSING:
            self.status_label.setText("Processando...")
            self.wave_visualizer.set_idle()
        elif state == AssistantState.SPEAKING:
            self.status_label.setText("Falando...")
            self.wave_visualizer.set_speaking()
    
    @pyqtSlot(str, MessageType)
    def on_message_received(self, message, message_type):
        """Manipula o recebimento de uma mensagem."""
        self.conversation_widget.add_message(message, message_type)


def create_icons():
    """Cria os ícones da aplicação."""
    # Este é um ícone mínimo para representar o assistente virtual
    # Em uma aplicação real, você substituiria isso por arquivos de ícone reais
    if not hasattr(sys, "_MEIPASS"):
        # Não estamos em um executável congelado
        base_path = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_path, "icons")
        
        # Cria o diretório de ícones se não existir
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
        
        # Cria um ícone simples se não existir
        icon_path = os.path.join(icons_dir, "icon.png")
        if not os.path.exists(icon_path):
            from PyQt6.QtGui import QImage, QPainter, QBrush, QColor
            
            # Cria uma imagem simples para o ícone
            img = QImage(64, 64, QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(img)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Desenha um círculo azul
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(4, 4, 56, 56)
            
            # Desenha um ícone de microfone (simplificado)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(24, 20, 16, 16)
            painter.drawRoundedRect(28, 36, 8, 14, 4, 4)
            
            painter.end()
            
            img.save(icon_path)
        
        # Registra o diretório de ícones no sistema de recursos
        from PyQt6.QtCore import QDir, QResource
        QResource.registerResource(os.path.join(base_path, "resources.qrc"))


def run_gui():
    """Executa a interface gráfica."""
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    
    # Cria os ícones
    create_icons()
    
    # Cria e mostra a janela principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
