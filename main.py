#тестовый тон
import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QSlider, QLabel, QWidget, 
                             QPushButton, QGroupBox, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pyaudio
import threading
import math

class AudioBooster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.is_playing = False
        self.boost_level = 1.0
        self.frequency = 440  # Hz
        self.phase = 0
        self.clipping_warning = False
        
        self.init_ui()
        self.setup_audio()
        
    def init_ui(self):
        self.setWindowTitle("Audio Booster - Генератор тона с усилением")
        self.setFixedSize(500, 450)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Статус
        self.status_label = QLabel("✅ Аудио инициализировано - Режим генератора тона")
        self.status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Предупреждение
        warning_label = QLabel("⚠️ ВНИМАНИЕ: Высокая громкость может повредить колонки!")
        warning_label.setStyleSheet("color: red; background-color: yellow; padding: 5px;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        # Группа управления тоном
        tone_group = QGroupBox("Настройки тона")
        tone_layout = QVBoxLayout(tone_group)
        
        # Частота
        tone_layout.addWidget(QLabel("Частота тона (Гц):"))
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setMinimum(50)
        self.freq_slider.setMaximum(2000)
        self.freq_slider.setValue(440)
        self.freq_slider.valueChanged.connect(self.update_frequency)
        tone_layout.addWidget(self.freq_slider)
        
        self.freq_label = QLabel("440 Гц (Нота Ля)")
        self.freq_label.setFont(QFont("Arial", 12))
        tone_layout.addWidget(self.freq_label)
        
        # Тип волны
        wave_layout = QHBoxLayout()
        wave_layout.addWidget(QLabel("Форма волны:"))
        self.wave_type = "sine"
        tone_layout.addLayout(wave_layout)
        
        layout.addWidget(tone_group)
        
        # Группа усиления
        boost_group = QGroupBox("Управление усилением")
        boost_layout = QVBoxLayout(boost_group)
        
        boost_layout.addWidget(QLabel("Уровень усиления:"))
        
        self.boost_slider = QSlider(Qt.Horizontal)
        self.boost_slider.setMinimum(100)
        self.boost_slider.setMaximum(1000)  # До 1000% 
        self.boost_slider.setValue(100)
        self.boost_slider.valueChanged.connect(self.update_boost)
        boost_layout.addWidget(self.boost_slider)
        
        # Отображение уровня
        boost_info_layout = QHBoxLayout()
        self.boost_label = QLabel("100%")
        self.boost_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        self.clipping_label = QLabel("✓ Нет клиппинга")
        self.clipping_label.setStyleSheet("color: green;")
        
        boost_info_layout.addWidget(self.boost_label)
        boost_info_layout.addWidget(self.clipping_label)
        boost_layout.addLayout(boost_info_layout)
        
        # Индикатор уровня
        self.level_layout = QHBoxLayout()
        self.level_layout.addWidget(QLabel("Уровень сигнала:"))
        self.level_bar = QLabel("▁▂▃▄▅▆▇")
        self.level_bar.setStyleSheet("color: green; font-size: 20px;")
        self.level_layout.addWidget(self.level_bar)
        self.level_layout.addStretch()
        boost_layout.addLayout(self.level_layout)
        
        layout.addWidget(boost_group)
        
        # Группа эквалайзера
        eq_group = QGroupBox("Дополнительные эффекты")
        eq_layout = QVBoxLayout(eq_group)
        
        self.bass_boost = QCheckBox("Вибрация басов (пульсация)")
        eq_layout.addWidget(self.bass_boost)
        
        self.tremolo = QCheckBox("Тремоло (колебание громкости)")
        eq_layout.addWidget(self.tremolo)
        
        layout.addWidget(eq_group)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Старт")
        self.start_btn.clicked.connect(self.toggle_audio)
        button_layout.addWidget(self.start_btn)
        
        test_btn = QPushButton("🔊 Тест")
        test_btn.clicked.connect(self.test_sound)
        button_layout.addWidget(test_btn)
        
        reset_btn = QPushButton("🔄 Сброс")
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
        # Информация
        info_label = QLabel(
            "Режим: Генератор тестового тона\n"
            "Используется для проверки усиления и качества звука"
        )
        info_label.setStyleSheet("color: gray; font-size: 10px; background-color: #F5F5F5; padding: 10px;")
        layout.addWidget(info_label)
        
    def setup_audio(self):
        """Инициализация аудио вывода"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            self.sample_rate = 44100
        except Exception as e:
            self.status_label.setText(f"❌ Ошибка аудио: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
    
    def update_boost(self, value):
        self.boost_level = value / 100.0
        self.boost_label.setText(f"{value}%")
        
        # Обновляем индикатор уровня
        level = min(value / 5, 100)  # Нормализуем для отображения
        bars = int(level / 15)
        level_bar = "▁▂▃▄▅▆▇"[:bars] + " " * (7 - bars)
        self.level_bar.setText(level_bar)
        
        # Меняем цвет в зависимости от уровня
        if value > 400:
            self.level_bar.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        elif value > 300:
            self.level_bar.setStyleSheet("color: orange; font-size: 20px;")
        elif value > 200:
            self.level_bar.setStyleSheet("color: yellow; font-size: 20px;")
        else:
            self.level_bar.setStyleSheet("color: green; font-size: 20px;")
    
    def update_frequency(self, value):
        self.frequency = value
        note = self.get_note_name(value)
        self.freq_label.setText(f"{value} Гц ({note})")
    
    def get_note_name(self, freq):
        """Получить название ноты по частоте"""
        notes = {
            261: "До", 277: "До#", 293: "Ре", 311: "Ре#", 
            329: "Ми", 349: "Фа", 370: "Фа#", 392: "Соль",
            415: "Соль#", 440: "Ля", 466: "Ля#", 493: "Си"
        }
        # Ищем ближайшую ноту
        closest_note = min(notes.keys(), key=lambda x: abs(x - freq))
        if abs(closest_note - freq) <= 10:  # Допуск 10 Гц
            return notes[closest_note]
        return ""
    
    def generate_waveform(self, frames):
        """Генерация waveform с текущими настройками"""
        t = np.arange(frames) / self.sample_rate
        wave = np.zeros(frames)
        
        # Основной тон
        if self.wave_type == "sine":
            wave = np.sin(2 * np.pi * self.frequency * t + self.phase)
        
        # Эффекты
        if self.bass_boost.isChecked():
            # Добавляем суб-гармонику
            wave += 0.3 * np.sin(2 * np.pi * self.frequency * 0.5 * t)
        
        if self.tremolo.isChecked():
            # Тремоло - модуляция амплитуды
            tremolo_depth = 0.3
            tremolo_rate = 5  # Hz
            wave *= (1 + tremolo_depth * np.sin(2 * np.pi * tremolo_rate * t))
        
        # Применяем усиление
        wave *= 0.7 * self.boost_level  # 0.7 чтобы избежать клиппинга на высоких уровнях
        
        # Проверка на клиппинг
        if np.max(np.abs(wave)) > 1.0:
            self.clipping_warning = True
            self.clipping_label.setText("⚠️ КЛИППИНГ!")
            self.clipping_label.setStyleSheet("color: red; font-weight: bold;")
            wave = np.clip(wave, -1.0, 1.0)
        else:
            self.clipping_warning = False
            self.clipping_label.setText("✓ Нет клиппинга")
            self.clipping_label.setStyleSheet("color: green;")
        
        # Обновляем фазу для плавного продолжения
        self.phase = (self.phase + 2 * np.pi * self.frequency * frames / self.sample_rate) % (2 * np.pi)
        
        return (wave * 32767).astype(np.int16)
    
    def audio_processing_thread(self):
        """Поток обработки аудио"""
        frames_per_buffer = 1024
        
        while self.is_playing:
            try:
                # Генерируем аудио данные
                audio_data = self.generate_waveform(frames_per_buffer)
                
                # Воспроизводим
                self.stream.write(audio_data.tobytes())
                
            except Exception as e:
                print(f"Audio error: {e}")
                break
    
    def toggle_audio(self):
        if not self.is_playing:
            self.is_playing = True
            self.start_btn.setText("⏹️ Стоп")
            self.phase = 0  # Сбрасываем фазу
            self.audio_thread = threading.Thread(target=self.audio_processing_thread)
            self.audio_thread.daemon = True
            self.audio_thread.start()
        else:
            self.is_playing = False
            self.start_btn.setText("▶️ Старт")
    
    def test_sound(self):
        """Короткий тестовый звук"""
        try:
            # Генерируем короткий импульс
            test_frames = 44100 // 2  # 0.5 секунды
            test_data = self.generate_waveform(test_frames)
            self.stream.write(test_data.tobytes())
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка теста: {e}")
    
    def reset_settings(self):
        self.boost_slider.setValue(100)
        self.freq_slider.setValue(440)
        self.bass_boost.setChecked(False)
        self.tremolo.setChecked(False)
        self.clipping_label.setText("✓ Нет клиппинга")
        self.clipping_label.setStyleSheet("color: green;")
        self.level_bar.setStyleSheet("color: green; font-size: 20px;")
    
    def closeEvent(self, event):
        self.is_playing = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    window = AudioBooster()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()