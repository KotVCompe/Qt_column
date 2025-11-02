import sys
import os
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QLabel, QWidget, QPushButton, 
                             QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt

class VBCableInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Установка VB-Cable для усиления системного звука")
        self.setFixedSize(700, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title = QLabel("🎵 Установка виртуального аудио кабеля")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: blue;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Инструкция
        instruction = QLabel(
            "Для усиления системного звука необходимо установить виртуальный аудио драйвер\n"
            "который будет перенаправлять звук из системы в программу усиления."
        )
        instruction.setStyleSheet("font-size: 12px; padding: 10px;")
        instruction.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction)
        
        # Шаги установки
        steps = QTextEdit()
        steps.setHtml("""
        <h3>📋 Пошаговая инструкция:</h3>
        <ol>
        <li><b>Скачайте VB-Cable</b> - нажмите кнопку "Скачать VB-Cable" ниже</li>
        <li><b>Распакуйте архив</b> в удобную папку</li>
        <li><b>Запустите установку</b> от имени администратора:
            <ul>
            <li>Для 64-битной Windows: <code>VBCABLE_Setup_x64.exe</code></li>
            <li>Для 32-битной Windows: <code>VBCABLE_Setup.exe</code></li>
            </ul>
        </li>
        <li><b>Перезагрузите компьютер</b> после установки</li>
        <li><b>Настройте звук в Windows</b>:
            <ul>
            <li>Откройте "Панель управления" → "Звук"</li>
            <li>На вкладке "Воспроизведение" установите "CABLE Input" как устройство по умолчанию</li>
            <li>На вкладке "Запись" убедитесь что "CABLE Output" включен</li>
            </ul>
        </li>
        <li><b>Запустите программу усиления звука</b> заново</li>
        </ol>
        
        <h3>🎯 Как это работает:</h3>
        <p>Системный звук → CABLE Input → CABLE Output → Программа усиления → Ваши колонки</p>
        
        <h3>⚠️ Важно:</h3>
        <ul>
        <li>Установка требует прав администратора</li>
        <li>После установки перезагрузите компьютер</li>
        <li>Не удаляйте VB-Cable пока используете программу усиления</li>
        </ul>
        """)
        steps.setReadOnly(True)
        layout.addWidget(steps)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        download_btn = QPushButton("🌐 Скачать VB-Cable")
        download_btn.clicked.connect(self.download_vb_cable)
        download_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;")
        button_layout.addWidget(download_btn)
        
        check_btn = QPushButton("🔍 Проверить установку")
        check_btn.clicked.connect(self.check_installation)
        check_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        button_layout.addWidget(check_btn)
        
        layout.addLayout(button_layout)
        
    def download_vb_cable(self):
        """Открывает страницу скачивания VB-Cable"""
        webbrowser.open("https://vb-audio.com/Cable/")
        QMessageBox.information(self, "Скачивание", 
                              "Открыта страница скачивания VB-Cable.\n\n"
                              "Скачайте архив и следуйте инструкциям выше.")
    
    def check_installation(self):
        """Проверяет установлен ли VB-Cable"""
        import pyaudio
        audio = pyaudio.PyAudio()
        
        vb_cable_found = False
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if 'cable' in info['name'].lower():
                vb_cable_found = True
                break
                
        audio.terminate()
        
        if vb_cable_found:
            QMessageBox.information(self, "Проверка", 
                                  "✅ VB-Cable обнаружен в системе!\n\n"
                                  "Теперь можно использовать программу усиления звука.")
        else:
            QMessageBox.warning(self, "Проверка", 
                              "❌ VB-Cable не найден!\n\n"
                              "Установите VB-Cable следуя инструкциям выше.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VBCableInstaller()
    window.show()
    sys.exit(app.exec_())