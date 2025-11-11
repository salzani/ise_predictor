import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QStackedWidget,
    QMessageBox, QScrollArea, QFrame, QRadioButton, QButtonGroup, QTextEdit
)
from PyQt6.QtGui import QDoubleValidator, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve

CSV_PATH = 'data/db/datasetEsgTRAIN.csv'
CSV_COLUMNS = [
    "ID", "EMPRESA", "SETOR", "USO_AGUA", "AREA", "AREA_RESERVA",
    "CO2_EMIT_DIR", "CO2_EMIT_INDIR", "CO2_REC", "INSUMO_QUIMICO_LEG",
    "INSUMO_QUIMICO_ORG", "BIODIVERSIDADE", "RESIDUO_REC", "RESIDUO_COMP",
    "RESIDUO_DESC", "ENERGIA_REN", "INDICE_SUSTENTABILIDADE"
]

# ============================================================================
# CHAT COMPONENTS
# ============================================================================

class ChatWorker(QThread):
    """Thread worker para processar respostas do chatbot sem bloquear a UI."""
    
    response_ready = pyqtSignal(str)
    
    def __init__(self, orchestrator, question):
        super().__init__()
        self.orchestrator = orchestrator
        self.question = question
    
    def run(self):
        """Executa a requisição ao modelo em thread separada."""
        response = self.orchestrator.get_response(self.question)
        self.response_ready.emit(response)


class MessageBubble(QWidget):
    """Widget de balão de mensagem para exibir mensagens do usuário e bot."""
    
    def __init__(self, text, is_user=True):
        super().__init__()
        self.setup_ui(text, is_user)
    
    def setup_ui(self, text, is_user):
        """Configura o layout e estilo do balão de mensagem."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)
        main_layout.setSpacing(2)
        
        bubble_layout = QHBoxLayout()
        bubble_layout.setContentsMargins(0, 0, 0, 0)

        bubble_frame = QFrame()
        bubble_content = QHBoxLayout(bubble_frame)
        bubble_content.setContentsMargins(16, 10, 16, 10)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setFont(QFont("Segoe UI", 10))
        label.setMaximumWidth(300)
        
        bubble_content.addWidget(label)
        
        if is_user:
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble_frame)
            
            bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #0066FF;
                    border-radius: 18px;
                }
            """)
            label.setStyleSheet("color: white; background: transparent;")

            username_layout = QHBoxLayout()
            username_layout.addStretch()
            username_label = QLabel("You")
            username_label.setFont(QFont("Segoe UI", 8))
            username_label.setStyleSheet("color: #666666; background: transparent;")
            username_layout.addWidget(username_label)
            username_layout.setContentsMargins(0, 0, 10, 0)
            
            main_layout.addLayout(bubble_layout)
            main_layout.addLayout(username_layout)
        else:
            bubble_layout.addWidget(bubble_frame)
            bubble_layout.addStretch()
            
            bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 18px;
                    padding: 1px;
                }
            """)

            label.setStyleSheet("color: #1a1a1a; background: transparent;")
 
            username_layout = QHBoxLayout()
            username_label = QLabel("ESG Assistant")
            username_label.setFont(QFont("Segoe UI", 8))
            username_label.setStyleSheet("color: #666666; background: transparent;")
            username_layout.addWidget(username_label)
            username_layout.addStretch()
            username_layout.setContentsMargins(10, 0, 0, 0)
            
            main_layout.addLayout(bubble_layout)
            main_layout.addLayout(username_layout)
        
        self.setStyleSheet("background: transparent;")


class ChatPanel(QWidget):
    """Painel do chatbot integrado."""
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Inicializa todos os componentes da interface do chat."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setStyleSheet("background-color: #F5F5F7;")
        
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E8E8E8;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(10)

        name_label = QLabel("ESG Assistant")
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        name_label.setStyleSheet("color: #1E293B; background: transparent;")

        status_label = QLabel("● Online")
        status_label.setFont(QFont("Segoe UI", 10))
        status_label.setStyleSheet("color: #10B981; background: transparent;")

        header_layout.addWidget(name_label)
        header_layout.addWidget(status_label)
        header_layout.addStretch()

        main_layout.addWidget(header_frame)
            
        self.setup_chat_area(main_layout)
        self.setup_input_area(main_layout)
    
    def setup_chat_area(self, parent_layout):
        """Configura a área de exibição de mensagens."""
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F5F5F7;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #CCCCCC;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #AAAAAA;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")

        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)

        self.scroll.setWidget(self.chat_container)
        parent_layout.addWidget(self.scroll)
    
    def setup_input_area(self, parent_layout):
        """Configura a área de entrada de texto e botões."""
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #E8E8E8;
            }
        """)
        input_frame.setFixedHeight(80)
        
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here")
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #F5F5F7;
                color: #1a1a1a;
                border: 1px solid #E8E8E8;
                border-radius: 20px;
                padding: 12px 20px;
            }
            QLineEdit:focus {
                background-color: white;
                border: 1px solid #0066FF;
                outline: none;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("▶")
        self.send_button.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.send_button.setFixedSize(45, 45)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #CCCCCC;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                color: #0066FF;
            }
            QPushButton:pressed {
                color: #0052CC;
            }
            QPushButton:disabled {
                color: #E8E8E8;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        parent_layout.addWidget(input_frame)
    
    def add_message(self, text, is_user=True):
        """Adiciona uma nova mensagem à área de chat."""
        bubble = MessageBubble(text, is_user)
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Processa o envio de mensagem do usuário."""
        text = self.input_field.text().strip()
        if not text or self.worker:
            return
        
        self.add_message(text, is_user=True)
        self.input_field.clear()
        self.set_input_enabled(False)
        
        self.worker = ChatWorker(self.orchestrator, text)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()
    
    def handle_response(self, response):
        """Processa a resposta recebida do chatbot."""
        self.add_message(response, is_user=False)
    
    def worker_finished(self):
        """Limpa o worker e reabilita a entrada após processamento."""
        self.worker = None
        self.set_input_enabled(True)
        self.input_field.setFocus()
    
    def set_input_enabled(self, enabled):
        """Habilita ou desabilita a área de entrada."""
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

class FloatingChatButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_chat_open = False
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedSize(60, 60)
        self.update_icon(False)
        self.setStyleSheet("""
            QPushButton {
                background-color: #0066FF;
                color: white;
                border: none;
                border-radius: 30px;
            }
            QPushButton:hover {
                background-color: #0052CC;
            }
            QPushButton:pressed {
                background-color: #003D99;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def update_icon(self, is_open):
        # Criar um ícone simples programaticamente
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if is_open:
            # Desenhar X
            pen = painter.pen()
            pen.setColor(QColor("white"))
            pen.setWidth(3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(10, 10, 30, 30)
            painter.drawLine(30, 10, 10, 30)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))

            from PyQt6.QtCore import QRectF
            painter.drawRoundedRect(QRectF(8, 8, 24, 18), 4, 4)

            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.moveTo(14, 26)  
            path.lineTo(10, 32)
            path.lineTo(18, 26)
            path.closeSubpath()
            painter.drawPath(path)

            painter.setBrush(QColor("#0066FF"))
            painter.drawEllipse(13, 14, 3, 3)
            painter.drawEllipse(19, 14, 3, 3)
            painter.drawEllipse(25, 14, 3, 3)
        
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setIconSize(pixmap.size())
        
    def toggle_icon(self, is_open):
        self.is_chat_open = is_open
        self.update_icon(is_open)


class InputWindow(QWidget):
    def __init__(self, stacked_widget, reg_tree, mlp_nn, xg_boost, preprocessor):
        super().__init__()
        self.stacked_widget = stacked_widget
        
        self.reg_tree = reg_tree
        self.mlp_nn = mlp_nn
        self.xg_boost = xg_boost
        self.preprocessor = preprocessor

        self.init_ui()
        self.final_df = None
        self.pred_arvore = None
        self.pred_mlp = None
        self.pred_xgboost = None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #F1F5F9; }
            QScrollBar:vertical { border: none; background-color: #E2E8F0; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background-color: #94A3B8; border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background-color: #64748B; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        scroll_content_widget = QWidget()
        scroll_content_widget.setStyleSheet("background-color: #F1F5F9;")
        layout = QVBoxLayout(scroll_content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(5)

        title_label = QLabel("ISE Predictor")
        title_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #0F172A; background: transparent; border: none;")

        subtitle_label = QLabel("Pedro Henrique Rodrigues Salzani, UNIFAJ")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #64748B; background: transparent; border: none;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_frame)

        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(25, 25, 25, 25)
        form_layout.setSpacing(20)

        self.inputs = {}

        input_style = """
            QLineEdit { 
                border: 1px solid #CBD5E1; 
                padding: 8px 12px; 
                border-radius: 6px; 
                background-color: #FFFFFF; 
                color: #1E293B; 
                font-size: 11px;
                min-height: 20px;
                max-height: 36px;
            } 
            QLineEdit:focus { 
                border: 2px solid #3B82F6; 
                background-color: #F8FAFF; 
            } 
            QLineEdit:hover { 
                border: 1px solid #94A3B8; 
            }
        """
        
        combo_style = """
            QComboBox { 
                border: 1px solid #CBD5E1; 
                padding: 8px 12px; 
                border-radius: 6px; 
                background-color: #FFFFFF; 
                color: #1E293B; 
                font-size: 11px;
                min-height: 20px;
                max-height: 36px;
            } 
            QComboBox:focus { 
                border: 2px solid #3B82F6; 
                background-color: #F8FAFF; 
            } 
            QComboBox:hover { 
                border: 1px solid #94A3B8; 
            }
            QComboBox::drop-down { 
                border: none; 
                width: 20px; 
                border-left: 1px solid #CBD5E1;
            }
            QComboBox QAbstractItemView { 
                border: 1px solid #CBD5E1; 
                background-color: #FFFFFF; 
                selection-background-color: #EFF6FF; 
                selection-color: #1E40AF; 
            }
        """

        label_style = "color: #475569; font-size: 11px; font-weight: 500; background: transparent; border: none;"

        section1 = QLabel("Basic info")
        section1.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        section1.setStyleSheet("color: #1E293B; padding: 5px 0px; border-bottom: 2px solid #3B82F6; background: transparent;")
        form_layout.addWidget(section1)

        grid1 = QGridLayout()
        grid1.setSpacing(15)
        grid1.setColumnStretch(1, 1)
        grid1.setColumnStretch(3, 1)
        grid1.setColumnStretch(5, 1)

        lbl_id = QLabel("ID:")
        lbl_id.setStyleSheet(label_style)
        self.inputs["ID"] = QLineEdit()
        self.inputs["ID"].setPlaceholderText("ID")
        self.inputs["ID"].setStyleSheet(input_style)
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.inputs["ID"].setValidator(validator)
        grid1.addWidget(lbl_id, 0, 0)
        grid1.addWidget(self.inputs["ID"], 0, 1)

        lbl_empresa = QLabel("Company:")
        lbl_empresa.setStyleSheet(label_style)
        self.inputs["EMPRESA"] = QLineEdit()
        self.inputs["EMPRESA"].setPlaceholderText("Company name")
        self.inputs["EMPRESA"].setStyleSheet(input_style)
        grid1.addWidget(lbl_empresa, 0, 2)
        grid1.addWidget(self.inputs["EMPRESA"], 0, 3)

        lbl_setor = QLabel("Setor:")
        lbl_setor.setStyleSheet(label_style)
        self.inputs["SETOR"] = QComboBox()
        self.inputs["SETOR"].addItems(["TRIGO", "MILHO", "SOJA", "CANA DE AÇUCAR"])
        self.inputs["SETOR"].setStyleSheet(combo_style)
        grid1.addWidget(lbl_setor, 0, 4)
        grid1.addWidget(self.inputs["SETOR"], 0, 5)

        form_layout.addLayout(grid1)

        section2 = QLabel("Natural Resources")
        section2.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        section2.setStyleSheet("color: #1E293B; padding: 5px 0px; border-bottom: 2px solid #10B981; background: transparent;")
        form_layout.addWidget(section2)

        grid2 = QGridLayout()
        grid2.setSpacing(15)
        grid2.setColumnStretch(1, 1)
        grid2.setColumnStretch(3, 1)

        resources = [
            ("USO_AGUA", "Water Usage (m³)"),
            ("AREA", "Total Area (ha)"),
            ("AREA_RESERVA", "Reserve Area (ha)"),
            ("BIODIVERSIDADE", "Biodiversity (0–1)")
        ]

        for i, (key, label_text) in enumerate(resources):
            row = i // 2
            col = (i % 2) * 2
            lbl = QLabel(label_text + ":")
            lbl.setStyleSheet(label_style)
            self.inputs[key] = QLineEdit()
            self.inputs[key].setPlaceholderText(label_text)
            self.inputs[key].setStyleSheet(input_style)
            validator = QDoubleValidator()
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            self.inputs[key].setValidator(validator)
            grid2.addWidget(lbl, row, col)
            grid2.addWidget(self.inputs[key], row, col + 1)

        form_layout.addLayout(grid2)

        section3 = QLabel("Carbon Emissions")
        section3.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        section3.setStyleSheet("color: #1E293B; padding: 5px 0px; border-bottom: 2px solid #F59E0B; background: transparent;")
        form_layout.addWidget(section3)

        grid3 = QGridLayout()
        grid3.setSpacing(15)
        grid3.setColumnStretch(1, 1)
        grid3.setColumnStretch(3, 1)
        grid3.setColumnStretch(5, 1)

        emissions = [
            ("CO2_EMIT_DIR", "Direct CO₂ Emission (t)"),
            ("CO2_EMIT_INDIR", "Indirect CO₂ Emission (t)"),
            ("CO2_REC", "CO₂ Removed (t)")
        ]

        for i, (key, label_text) in enumerate(emissions):
            col = i * 2
            lbl = QLabel(label_text + ":")
            lbl.setStyleSheet(label_style)
            self.inputs[key] = QLineEdit()
            self.inputs[key].setPlaceholderText(label_text)
            self.inputs[key].setStyleSheet(input_style)
            validator = QDoubleValidator()
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            self.inputs[key].setValidator(validator)
            grid3.addWidget(lbl, 0, col)
            grid3.addWidget(self.inputs[key], 0, col + 1)

        form_layout.addLayout(grid3)

        section4 = QLabel("Inputs and Waste")
        section4.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        section4.setStyleSheet("color: #1E293B; padding: 5px 0px; border-bottom: 2px solid #8B5CF6; background: transparent;")
        form_layout.addWidget(section4)

        grid4 = QGridLayout()
        grid4.setSpacing(15)
        grid4.setColumnStretch(1, 1)
        grid4.setColumnStretch(3, 1)

        waste = [
            ("INSUMO_QUIMICO_LEG", "Legal Chemical Input (kg)"),
            ("INSUMO_QUIMICO_ORG", "Organic Chemical Input (kg)"),
            ("RESIDUO_REC", "Recycled Waste (t)"),
            ("RESIDUO_COMP", "Composted Waste (t)"),
            ("RESIDUO_DESC", "Disposed Waste (t)"),
            ("ENERGIA_REN", "Renewable Energy (%)")
        ]

        for i, (key, label_text) in enumerate(waste):
            row = i // 2
            col = (i % 2) * 2
            lbl = QLabel(label_text + ":")
            lbl.setStyleSheet(label_style)
            self.inputs[key] = QLineEdit()
            self.inputs[key].setPlaceholderText(label_text)
            self.inputs[key].setStyleSheet(input_style)
            validator = QDoubleValidator()
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            self.inputs[key].setValidator(validator)
            grid4.addWidget(lbl, row, col)
            grid4.addWidget(self.inputs[key], row, col + 1)

        form_layout.addLayout(grid4)

        section5 = QLabel("Sustainability")
        section5.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        section5.setStyleSheet("color: #1E293B; padding: 5px 0px; border-bottom: 2px solid #EF4444; background: transparent;")
        form_layout.addWidget(section5)

        grid5 = QGridLayout()
        grid5.setSpacing(15)
        grid5.setColumnStretch(1, 1)

        lbl_indice = QLabel("Sustainability Index (0-100):")
        lbl_indice.setStyleSheet(label_style)
        self.inputs["INDICE_SUSTENTABILIDADE"] = QLineEdit()
        self.inputs["INDICE_SUSTENTABILIDADE"].setPlaceholderText("Sustainability Index")
        self.inputs["INDICE_SUSTENTABILIDADE"].setStyleSheet(input_style)
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.inputs["INDICE_SUSTENTABILIDADE"].setValidator(validator)
        grid5.addWidget(lbl_indice, 0, 0)
        grid5.addWidget(self.inputs["INDICE_SUSTENTABILIDADE"], 0, 1)

        form_layout.addLayout(grid5)
        layout.addWidget(form_frame)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        autocomplete_button = QPushButton("Autocomplete (Test)")
        autocomplete_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        autocomplete_button.setMinimumHeight(45)
        autocomplete_button.setStyleSheet("""
            QPushButton { 
                background-color: #64748B; 
                color: #FFFFFF; 
                border: none; 
                padding: 12px 24px; 
                border-radius: 8px; 
            } 
            QPushButton:hover { 
                background-color: #475569; 
            } 
            QPushButton:pressed { 
                background-color: #334155; 
            }
        """)
        autocomplete_button.clicked.connect(self.autocomplete_fields)

        submit_button = QPushButton("Send Data and View Predictions")
        submit_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        submit_button.setMinimumHeight(45)
        submit_button.setStyleSheet("""
            QPushButton { 
                background-color: #3B82F6; 
                color: #FFFFFF; 
                border: none; 
                padding: 12px 24px; 
                border-radius: 8px; 
            } 
            QPushButton:hover { 
                background-color: #2563EB; 
            } 
            QPushButton:pressed { 
                background-color: #1D4ED8; 
            }
        """)
        submit_button.clicked.connect(self.submit_data)

        button_layout.addStretch()
        button_layout.addWidget(autocomplete_button)
        button_layout.addWidget(submit_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def autocomplete_fields(self):
        """Preenche os campos com dados de teste"""
        test_data = {
            "ID": "0.0",
            "EMPRESA": "EMPRESA00342",
            "SETOR": "TRIGO",
            "USO_AGUA": "5.58",
            "AREA": "8138.78",
            "AREA_RESERVA": "8.12",
            "CO2_EMIT_DIR": "5.62",
            "CO2_EMIT_INDIR": "4.84",
            "CO2_REC": "6.12",
            "INSUMO_QUIMICO_LEG": "6.83",
            "INSUMO_QUIMICO_ORG": "5.89",
            "BIODIVERSIDADE": "11.13",
            "RESIDUO_REC": "12.13",
            "RESIDUO_COMP": "37.62",
            "RESIDUO_DESC": "14.79",
            "ENERGIA_REN": "47.98",
            "INDICE_SUSTENTABILIDADE": "0.58"
        }

        for key, value in test_data.items():
            if key in self.inputs:
                widget = self.inputs[key]
                if isinstance(widget, QLineEdit):
                    widget.setText(value)
                elif isinstance(widget, QComboBox):
                    index = widget.findText(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)

    def submit_data(self):
        data_values = {}
        all_fields_valid = True

        for label_text, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                value_text = widget.text().strip().replace(',', '.')
                if not value_text:
                    QMessageBox.warning(self, "Empty field", f"The field '{label_text.replace('_', ' ').title()}' cannot be empty.")
                    all_fields_valid = False; widget.setFocus(); return
                if label_text not in ["EMPRESA", "SETOR"]:
                    try:
                        data_values[label_text] = float(value_text)
                    except ValueError:
                        QMessageBox.warning(self, "Validation error", f"The field '{label_text.replace('_', ' ').title()}' must be a valid number.")
                        all_fields_valid = False; widget.setFocus(); return
                else: 
                    data_values[label_text] = value_text
            elif isinstance(widget, QComboBox):
                data_values[label_text] = widget.currentText()

        if all_fields_valid:
            self.final_df = pd.DataFrame([data_values])
            current_cols_ordered = [col for col in CSV_COLUMNS if col in self.final_df.columns]
            self.final_df = self.final_df[current_cols_ordered]

            try:
                self.pred_arvore = self.reg_tree.predict_tree(self.final_df.copy())
                self.pred_mlp = self.mlp_nn.predict_mlp(self.final_df.copy(), self.preprocessor)
                self.pred_xgboost = self.xg_boost.predict_xgboost(self.final_df.copy())
                
                if isinstance(self.pred_arvore, (list, pd.Series, pd.DataFrame)): self.pred_arvore = self.pred_arvore[0]
                if isinstance(self.pred_mlp, (list, pd.Series, pd.DataFrame)): self.pred_mlp = self.pred_mlp[0]
                if isinstance(self.pred_xgboost, (list, pd.Series, pd.DataFrame)): self.pred_xgboost = self.pred_xgboost[0]

                print(f"Tree prediction: {self.pred_arvore}, Tipo: {type(self.pred_arvore)}")
                print(f"MLP prediction: {self.pred_mlp}, Tipo: {type(self.pred_mlp)}")
                print(f"XGBoost prediction: {self.pred_xgboost}, Tipo: {type(self.pred_xgboost)}")

                results_w = self.stacked_widget.widget(1)
                if isinstance(results_w, ResultsAndSaveWindow):
                    results_w.set_data(self.final_df.copy(), float(self.pred_arvore), float(self.pred_mlp), float(self.pred_xgboost))
                    self.stacked_widget.setCurrentIndex(1)
                else:
                    QMessageBox.critical(self, "Erro", "Error")

            except Exception as e:
                QMessageBox.critical(self, "Prediction error", f"An error occurred while generating the predictions.: {e}")
                print(f"An error occurred while generating the predictions.: {e}")

    def clear_fields(self):
        for widget in self.inputs.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        self.final_df = None
        self.pred_arvore = None
        self.pred_mlp = None
        self.pred_xgboost = None


class ResultsAndSaveWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.original_data_df = None
        self.pred_tree_val = None
        self.pred_mlp_val = None
        self.pred_xgboost_val = None
        self.user_indice_val = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #F1F5F9; }
            QScrollBar:vertical { border: none; background-color: #E2E8F0; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background-color: #94A3B8; border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background-color: #64748B; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        scroll_content_widget = QWidget()
        scroll_content_widget.setStyleSheet("background-color: #F1F5F9;")
        layout = QVBoxLayout(scroll_content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(5)

        title_label = QLabel("Predictive Analysis Completed")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #0F172A; background: transparent; border: none;")

        header_layout.addWidget(title_label)
        layout.addWidget(header_frame)

        results_frame = QFrame()
        results_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(30, 25, 30, 25)
        results_layout.setSpacing(20)

        results_title = QLabel("Prediction Results")
        results_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        results_title.setStyleSheet("color: #1E293B; background: transparent; border: none;")
        results_layout.addWidget(results_title)

        results_grid = QGridLayout()
        results_grid.setSpacing(15)
        results_grid.setColumnStretch(0, 1)
        results_grid.setColumnStretch(1, 1)
        results_grid.setColumnStretch(2, 1)
        results_grid.setColumnStretch(3, 1)

        label_style = "color: #64748B; font-size: 11px; font-weight: 500; background: transparent; border: none;"
        value_style = "color: #0F172A; font-size: 18px; font-weight: 700; background: transparent; border: none; padding: 8px 0px;"

        tree_label = QLabel("Regression Tree")
        tree_label.setStyleSheet(label_style)
        self.label_pred_tree = QLabel("0.00")
        self.label_pred_tree.setStyleSheet(value_style)
        results_grid.addWidget(tree_label, 0, 0)
        results_grid.addWidget(self.label_pred_tree, 1, 0)

        mlp_label = QLabel("Multi Layer Perceptron")
        mlp_label.setStyleSheet(label_style)
        self.label_pred_mlp = QLabel("0.00")
        self.label_pred_mlp.setStyleSheet(value_style)
        results_grid.addWidget(mlp_label, 0, 1)
        results_grid.addWidget(self.label_pred_mlp, 1, 1)

        xgb_label = QLabel("XGBoost")
        xgb_label.setStyleSheet(label_style)
        self.label_pred_xgboost = QLabel("0.00")
        self.label_pred_xgboost.setStyleSheet(value_style)
        results_grid.addWidget(xgb_label, 0, 2)
        results_grid.addWidget(self.label_pred_xgboost, 1, 2)

        user_label = QLabel("Original value")
        user_label.setStyleSheet(label_style)
        self.label_user_value = QLabel("0.00")
        self.label_user_value.setStyleSheet(value_style)
        results_grid.addWidget(user_label, 0, 3)
        results_grid.addWidget(self.label_user_value, 1, 3)

        results_layout.addLayout(results_grid)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        results_layout.addWidget(separator)

        choice_label = QLabel("Choose the value to be saved.:")
        choice_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        choice_label.setStyleSheet("color: #1E293B; background: transparent; border: none; padding-top: 10px;")
        results_layout.addWidget(choice_label)

        self.radio_group = QButtonGroup(self)
        
        radio_button_style = """
        QRadioButton { 
            color: #475569; 
            background-color: transparent; 
            border: none; 
            padding: 6px 8px; 
            font-size: 11px;
        } 
        QRadioButton::indicator { 
            width: 16px; 
            height: 16px; 
            border-radius: 8px;
            border: 2px solid #CBD5E1; 
            background-color: #FFFFFF;
        }
        QRadioButton::indicator:checked { 
            background-color: #3B82F6; 
            border: 2px solid #3B82F6;
        }
        QRadioButton::indicator:hover { 
            border: 2px solid #93C5FD; 
        }
        """

        self.rb_tree = QRadioButton("Use Regression Tree Prediction")
        self.rb_tree.setFont(QFont("Segoe UI", 11))
        self.rb_tree.setStyleSheet(radio_button_style)
        
        self.rb_mlp = QRadioButton("Use MLP Prediction")
        self.rb_mlp.setFont(QFont("Segoe UI", 11))
        self.rb_mlp.setStyleSheet(radio_button_style)

        self.rb_xgboost = QRadioButton("Use XGBoost Prediction")
        self.rb_xgboost.setFont(QFont("Segoe UI", 11))
        self.rb_xgboost.setStyleSheet(radio_button_style)
        
        self.rb_all = QRadioButton("Save all predictions (three separate entries)")
        self.rb_all.setFont(QFont("Segoe UI", 11))
        self.rb_all.setStyleSheet(radio_button_style)
        
        self.rb_user = QRadioButton("Keep Original Value Entered")
        self.rb_user.setFont(QFont("Segoe UI", 11))
        self.rb_user.setStyleSheet(radio_button_style)
        self.rb_user.setChecked(True)

        self.radio_group.addButton(self.rb_tree, 1)
        self.radio_group.addButton(self.rb_mlp, 2)
        self.radio_group.addButton(self.rb_xgboost, 3)
        self.radio_group.addButton(self.rb_all, 4)
        self.radio_group.addButton(self.rb_user, 5)
        
        radio_layout = QVBoxLayout()
        radio_layout.setSpacing(8)
        radio_layout.addWidget(self.rb_tree)
        radio_layout.addWidget(self.rb_mlp)
        radio_layout.addWidget(self.rb_xgboost)
        radio_layout.addWidget(self.rb_all)
        radio_layout.addWidget(self.rb_user)
        results_layout.addLayout(radio_layout)

        layout.addWidget(results_frame)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        discard_button = QPushButton("Discard and New Registration")
        discard_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        discard_button.setMinimumHeight(45)
        discard_button.setStyleSheet("""
            QPushButton { 
                background-color: #FFFFFF; 
                color: #64748B; 
                border: 2px solid #E2E8F0; 
                padding: 12px 32px; 
                border-radius: 8px; 
            } 
            QPushButton:hover { 
                background-color: #F8FAFC; 
                border: 2px solid #CBD5E1;
                color: #475569;
            } 
            QPushButton:pressed { 
                background-color: #F1F5F9; 
            }
        """)
        discard_button.clicked.connect(self.discard_and_new)

        save_button = QPushButton("Confirm and Save Data")
        save_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        save_button.setMinimumHeight(45)
        save_button.setStyleSheet("""
            QPushButton { 
                background-color: #10B981; 
                color: #FFFFFF; 
                border: none; 
                padding: 12px 32px; 
                border-radius: 8px; 
            } 
            QPushButton:hover { 
                background-color: #059669; 
            } 
            QPushButton:pressed { 
                background-color: #047857; 
            }
        """)
        save_button.clicked.connect(self.save_choice_and_proceed)

        buttons_layout.addStretch()
        buttons_layout.addWidget(discard_button)
        buttons_layout.addWidget(save_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
    def set_data(self, data_df, pred_tree, pred_mlp, pred_xgboost):
        self.original_data_df = data_df
        self.pred_tree_val = pred_tree
        self.pred_mlp_val = pred_mlp
        self.pred_xgboost_val = pred_xgboost
        self.user_indice_val = self.original_data_df["INDICE_SUSTENTABILIDADE"].iloc[0]

        self.label_pred_tree.setText(f"{self.pred_tree_val:.2f}")
        self.label_pred_mlp.setText(f"{self.pred_mlp_val:.2f}")
        self.label_pred_xgboost.setText(f"{self.pred_xgboost_val:.2f}")
        self.label_user_value.setText(f"{self.user_indice_val:.2f}")
        self.rb_user.setChecked(True)

    def discard_and_new(self):
        reply = QMessageBox.question(
            self, 
            "Confirm Discard",
            "Are you sure you want to discard the current data?\nAll entered data will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_input_fields_and_go_back()

    def append_to_csv(self, df_new_row):
        try:
            df_new_row_ordered = df_new_row[CSV_COLUMNS]
            
            try:
                df_existing = pd.read_csv(CSV_PATH)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                df_existing = pd.DataFrame(columns=CSV_COLUMNS)

            df_combined = pd.concat([df_existing, df_new_row_ordered], ignore_index=True)
            df_combined.to_csv(CSV_PATH, index=False, columns=CSV_COLUMNS)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Unable to save the data to the CSV: {e}")
            print(f"Erro detalhado ao salvar no CSV: {e}")
            return False

    def save_choice_and_proceed(self):
        if self.original_data_df is None:
            QMessageBox.warning(self, "No Data", "There is no data to save.")
            return

        selected_id = self.radio_group.checkedId()
        saved_successfully = False

        if selected_id == 1:
            df_to_save = self.original_data_df.copy()
            df_to_save["INDICE_SUSTENTABILIDADE"] = round(self.pred_tree_val, 2)
            if self.append_to_csv(df_to_save):
                QMessageBox.information(self, "Saved Successfully", "✅ Data saved with the Regression Tree prediction.")
                saved_successfully = True
                
        elif selected_id == 2:
            df_to_save = self.original_data_df.copy()
            df_to_save["INDICE_SUSTENTABILIDADE"] = round(self.pred_mlp_val, 2)
            if self.append_to_csv(df_to_save):
                QMessageBox.information(self, "Saved Successfully", "✅ Data saved with the MLP prediction.")
                saved_successfully = True

        elif selected_id == 3:
            df_to_save = self.original_data_df.copy()
            df_to_save["INDICE_SUSTENTABILIDADE"] = round(self.pred_xgboost_val, 2)
            if self.append_to_csv(df_to_save):
                QMessageBox.information(self, "Saved Successfully", "✅ Data saved with the XGBoost prediction.")
                saved_successfully = True

        elif selected_id == 4:
            df_tree = self.original_data_df.copy()
            df_tree["INDICE_SUSTENTABILIDADE"] = round(self.pred_tree_val, 2)
            
            df_mlp = self.original_data_df.copy()
            df_mlp["INDICE_SUSTENTABILIDADE"] = round(self.pred_mlp_val, 2)

            df_xgboost = self.original_data_df.copy()
            df_xgboost["INDICE_SUSTENTABILIDADE"] = round(self.pred_xgboost_val, 2)

            try:
                df_existing = pd.read_csv(CSV_PATH)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                 df_existing = pd.DataFrame(columns=CSV_COLUMNS)

            df_combined = pd.concat([df_existing, df_tree[CSV_COLUMNS], df_mlp[CSV_COLUMNS], df_xgboost[CSV_COLUMNS]], ignore_index=True)
            try:
                df_combined.to_csv(CSV_PATH, index=False, columns=CSV_COLUMNS)
                QMessageBox.information(self, "Saved Successfully", "✅ The three predictions were saved as separate entries.")
                saved_successfully = True
            except Exception as e:
                 QMessageBox.critical(self, "Save error", f"Error to save the entries: {e}")

        elif selected_id == 5:
            df_to_save = self.original_data_df.copy()
            if self.append_to_csv(df_to_save):
                QMessageBox.information(self, "Saved Successfully", "✅ Data saved with the original entered value.")
                saved_successfully = True
        else:
            QMessageBox.warning(self, "error", "Please select one of the options")
            return

        if saved_successfully:
            self.clear_input_fields_and_go_back()

    def clear_input_fields_and_go_back(self):
        input_w = self.stacked_widget.widget(0)
        if isinstance(input_w, InputWindow):
            input_w.clear_fields()
        self.stacked_widget.setCurrentIndex(0)

class IntegratedMainWindow(QWidget):
    def __init__(self, reg_tree, mlp_nn, xg_boost, preprocessor, orchestrator):
        super().__init__()
        self.setWindowTitle("ESG Platform")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("background-color: #F1F5F9;")
        
        self.is_chat_visible = False

        self.main_horizontal = QHBoxLayout(self)
        self.main_horizontal.setContentsMargins(0, 0, 0, 0)
        self.main_horizontal.setSpacing(0)

        self.chat_panel = ChatPanel(orchestrator)
        self.chat_panel.setFixedWidth(0)
        self.chat_panel.setVisible(False)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.VLine)
        self.separator.setStyleSheet("background-color: #E2E8F0; max-width: 1px;")
        self.separator.setVisible(False)

        self.form_stacked_widget = QStackedWidget()
        self.input_window = InputWindow(self.form_stacked_widget, reg_tree, mlp_nn, xg_boost, preprocessor)
        self.results_save_window = ResultsAndSaveWindow(self.form_stacked_widget)

        self.form_stacked_widget.addWidget(self.input_window)
        self.form_stacked_widget.addWidget(self.results_save_window)

        self.main_horizontal.addWidget(self.chat_panel)
        self.main_horizontal.addWidget(self.separator)
        self.main_horizontal.addWidget(self.form_stacked_widget)

        self.setLayout(self.main_horizontal)
 
        self.chat_button = FloatingChatButton(self)
        self.chat_button.clicked.connect(self.toggle_chat)
        self.chat_button.setFixedSize(60, 60)
        self.chat_button.raise_() 

        QTimer.singleShot(100, self.position_chat_button)

    def position_chat_button(self):
        margin = 30
        button_x = self.width() - self.chat_button.width() - margin
        button_y = self.height() - self.chat_button.height() - margin
        self.chat_button.move(button_x, button_y)
        self.chat_button.show() 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'chat_button'):
            self.position_chat_button()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'chat_button'):
            self.position_chat_button()

    def toggle_chat(self):
        if self.is_chat_visible:
            # Fechar o chat
            self.animate_chat(450, 0)
            self.is_chat_visible = False
            self.chat_button.toggle_icon(False)
            QTimer.singleShot(300, lambda: self.chat_panel.setVisible(False))
            QTimer.singleShot(300, lambda: self.separator.setVisible(False))
        else:
            self.chat_panel.setVisible(True)
            self.separator.setVisible(True)
            self.animate_chat(0, 450)
            self.is_chat_visible = True
            self.chat_button.toggle_icon(True)
            QTimer.singleShot(350, lambda: self.chat_panel.input_field.setFocus())

    def animate_chat(self, start_width, end_width):
        self.animation = QPropertyAnimation(self.chat_panel, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self.animation_max = QPropertyAnimation(self.chat_panel, b"maximumWidth")
        self.animation_max.setDuration(300)
        self.animation_max.setStartValue(start_width)
        self.animation_max.setEndValue(end_width)
        self.animation_max.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self.animation.start()
        self.animation_max.start()