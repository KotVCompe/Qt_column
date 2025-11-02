import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QSlider, QLabel, QWidget, 
                             QPushButton, QMessageBox, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyaudio
import threading
import time

class AudioBridgeEnhanced(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.is_playing = False
        self.boost_level = 1.0
        self.input_stream = None
        self.output_stream = None
        self.soft_clip = True  # Мягкое ограничение
        self.pre_boost = 1.0   # Предварительное усиление
        
        self.init_ui()
        self.scan_audio_devices()
        
    def init_ui(self):
        self.setWindowTitle("Audio Bridge Enhanced - Супер Усилитель звука")
        self.setFixedSize(700, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("font-weight: bold; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Выбор устройств
        devices_group = QWidget()
        devices_layout = QVBoxLayout(devices_group)
        
        # Выбор входного устройства
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Устройство захвата:"))
        self.input_combo = QComboBox()
        input_layout.addWidget(self.input_combo)
        devices_layout.addLayout(input_layout)
        
        # Выбор выходного устройства
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Устройство вывода:"))
        self.output_combo = QComboBox()
        output_layout.addWidget(self.output_combo)
        devices_layout.addLayout(output_layout)
        
        layout.addWidget(devices_group)
        
        # Предварительное усиление
        layout.addWidget(QLabel("Предварительное усиление (базовое):"))
        
        self.pre_boost_slider = QSlider(Qt.Horizontal)
        self.pre_boost_slider.setMinimum(100)
        self.pre_boost_slider.setMaximum(500)  # До 5x предварительного усиления
        self.pre_boost_slider.setValue(100)
        self.pre_boost_slider.valueChanged.connect(self.update_pre_boost)
        layout.addWidget(self.pre_boost_slider)
        
        self.pre_boost_label = QLabel("100%")
        self.pre_boost_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.pre_boost_label)
        
        # Основное усиление
        layout.addWidget(QLabel("Основное усиление:"))
        
        self.boost_slider = QSlider(Qt.Horizontal)
        self.boost_slider.setMinimum(100)
        self.boost_slider.setMaximum(2000)  # Увеличил максимальное усиление до 20x
        self.boost_slider.setValue(100)
        self.boost_slider.valueChanged.connect(self.update_boost)
        layout.addWidget(self.boost_slider)
        
        self.boost_label = QLabel("100%")
        self.boost_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.boost_label)
        
        # Общее усиление
        self.total_boost_label = QLabel("Общее усиление: 100%")
        self.total_boost_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_boost_label.setStyleSheet("color: #FF6600;")
        layout.addWidget(self.total_boost_label)
        
        # Опции обработки
        options_layout = QHBoxLayout()
        
        self.soft_clip_check = QCheckBox("Мягкое ограничение (рекомендуется)")
        self.soft_clip_check.setChecked(True)
        self.soft_clip_check.stateChanged.connect(self.toggle_soft_clip)
        options_layout.addWidget(self.soft_clip_check)
        
        self.aggressive_boost_check = QCheckBox("Агрессивное усиление")
        self.aggressive_boost_check.stateChanged.connect(self.toggle_aggressive_boost)
        options_layout.addWidget(self.aggressive_boost_check)
        
        layout.addLayout(options_layout)
        
        # Индикатор уровня
        level_layout = QVBoxLayout()
        level_layout.addWidget(QLabel("Уровень сигнала:"))
        
        self.level_meter = QLabel("░░░░░░░░░░")
        self.level_meter.setFont(QFont("Arial", 20))
        self.level_meter.setStyleSheet("color: #00FF00;")
        level_layout.addWidget(self.level_meter)
        
        self.level_db = QLabel("Уровень: -- dB")
        level_layout.addWidget(self.level_db)
        
        layout.addLayout(level_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🎵 Старт супер-усиление")
        self.start_btn.clicked.connect(self.toggle_audio)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.start_btn)
        
        refresh_btn = QPushButton("🔄 Обновить устройства")
        refresh_btn.clicked.connect(self.scan_audio_devices)
        button_layout.addWidget(refresh_btn)
        
        test_btn = QPushButton("🔊 Тест звука")
        test_btn.clicked.connect(self.test_audio)
        button_layout.addWidget(test_btn)
        
        layout.addLayout(button_layout)
        
        # Предупреждение
        warning = QLabel("⚠️ ВНИМАНИЕ: Высокое усиление может повредить динамики!")
        warning.setStyleSheet("background-color: #FFF8DC; padding: 10px; font-weight: bold; color: #FF0000;")
        layout.addWidget(warning)
        
    def update_pre_boost(self, value):
        self.pre_boost = value / 100.0
        self.pre_boost_label.setText(f"{value}%")
        self.update_total_boost()
    
    def update_boost(self, value):
        self.boost_level = value / 100.0
        self.boost_label.setText(f"{value}%")
        self.update_total_boost()
    
    def update_total_boost(self):
        total = self.pre_boost * self.boost_level
        self.total_boost_label.setText(f"Общее усиление: {total:.1f}x ({int(total * 100)}%)")
        
        # Изменяем цвет в зависимости от уровня усиления
        if total > 10:
            color = "#FF0000"
        elif total > 5:
            color = "#FF6600"
        elif total > 2:
            color = "#FFAA00"
        else:
            color = "#00AA00"
            
        self.total_boost_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def toggle_soft_clip(self, state):
        self.soft_clip = (state == Qt.Checked)
    
    def toggle_aggressive_boost(self, state):
        if state == Qt.Checked:
            # Автоматически настраиваем для агрессивного усиления
            self.pre_boost_slider.setValue(200)  # 2x предварительное усиление
            self.boost_slider.setValue(1500)     # 15x основное усиление
            self.soft_clip_check.setChecked(True)
    
    def soft_clipper(self, audio_data):
        """Мягкое ограничение для предотвращения резкого клиппинга"""
        threshold = 0.8
        return np.tanh(audio_data * threshold) / threshold
    
    def hard_clip(self, audio_data):
        """Жесткое ограничение"""
        return np.clip(audio_data, -0.99, 0.99)
    
    def scan_audio_devices(self):
        """Сканирование аудио устройств"""
        self.input_combo.clear()
        self.output_combo.clear()
        
        input_devices = []
        output_devices = []
        cable_devices = []
        
        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
                name = info['name']
                
                # Проверяем поддержку формата
                try:
                    is_input = info['maxInputChannels'] > 0
                    is_output = info['maxOutputChannels'] > 0
                except:
                    continue
                
                if is_input:
                    device_text = f"{i}: {name} (вход)"
                    self.input_combo.addItem(device_text, i)
                    input_devices.append((i, name))
                    if 'cable' in name.lower():
                        cable_devices.append((i, name))
                
                if is_output:
                    device_text = f"{i}: {name} (выход)"
                    self.output_combo.addItem(device_text, i)
                    output_devices.append((i, name))
                    
            except Exception as e:
                print(f"Error scanning device {i}: {e}")
        
        # Автоматически выбираем VB-Cable если найден
        for i in range(self.input_combo.count()):
            if 'cable' in self.input_combo.itemText(i).lower():
                self.input_combo.setCurrentIndex(i)
                break
        
        # Автоматически выбираем первое выходное устройство
        if self.output_combo.count() > 0:
            self.output_combo.setCurrentIndex(0)
            
        status = f"Найдено: {len(input_devices)} входов, {len(output_devices)} выходов"
        if cable_devices:
            status += " ✅ VB-Cable найден"
        else:
            status += " ❌ VB-Cable не найден"
            
        self.status_label.setText(status)
    
    def safe_open_stream(self, device_index, is_input, rate=44100):
        """Безопасное открытие аудио потока"""
        try:
            if is_input:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=2,
                    rate=rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024,
                    stream_callback=None
                )
            else:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=2,
                    rate=rate,
                    output=True,
                    output_device_index=device_index,
                    frames_per_buffer=1024,
                    stream_callback=None
                )
            return stream
        except Exception as e:
            print(f"Error opening stream: {e}")
            # Попробуем с другими параметрами
            try:
                if is_input:
                    stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=22050,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=512
                    )
                else:
                    stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=22050,
                        output=True,
                        output_device_index=device_index,
                        frames_per_buffer=512
                    )
                return stream
            except Exception as e2:
                raise Exception(f"Не удалось открыть аудио поток: {e2}")
    
    def toggle_audio(self):
        if not self.is_playing:
            self.start_audio()
        else:
            self.stop_audio()
    
    def start_audio(self):
        """Запуск аудио моста"""
        try:
            # Получаем выбранные устройства
            input_index = self.input_combo.currentData()
            output_index = self.output_combo.currentData()
            
            if input_index is None or output_index is None:
                QMessageBox.warning(self, "Ошибка", "Выберите входное и выходное устройства!")
                return
            
            # Закрываем предыдущие потоки если они есть
            self.stop_audio()
            
            # Даем время на закрытие потоков
            time.sleep(0.1)
            
            # Открываем новые потоки
            self.input_stream = self.safe_open_stream(input_index, is_input=True)
            self.output_stream = self.safe_open_stream(output_index, is_input=False)
            
            self.is_playing = True
            self.start_btn.setText("⏹️ Стоп усиление")
            self.start_btn.setStyleSheet("QPushButton { background-color: #FF4444; color: white; font-weight: bold; }")
            self.status_label.setText("🎵 СУПЕР-УСИЛЕНИЕ АКТИВНО!")
            self.status_label.setStyleSheet("color: red; font-weight: bold; background-color: yellow;")
            
            # Запускаем поток обработки
            self.audio_thread = threading.Thread(target=self.audio_processing_loop)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить аудио:\n{str(e)}")
    
    def audio_processing_loop(self):
        """Цикл обработки аудио с улучшенным усилением"""
        error_count = 0
        max_errors = 5
        
        while self.is_playing and error_count < max_errors:
            try:
                # Читаем данные
                data = self.input_stream.read(1024, exception_on_overflow=False)
                
                # Конвертируем в numpy массив
                audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                
                # Нормализуем до [-1, 1]
                audio_normalized = audio_array / 32768.0
                
                # Применяем предварительное усиление
                audio_boosted = audio_normalized * self.pre_boost
                
                # Применяем основное усиление
                audio_boosted *= self.boost_level
                
                # Применяем ограничение
                if self.soft_clip:
                    audio_boosted = self.soft_clipper(audio_boosted)
                else:
                    audio_boosted = self.hard_clip(audio_boosted)
                
                # Конвертируем обратно в int16
                audio_final = (audio_boosted * 32767.0).astype(np.int16)
                
                # Рассчитываем уровень сигнала
                if len(audio_array) > 0:
                    rms = np.sqrt(np.mean(audio_normalized**2))
                    if rms > 0:
                        db = 20 * np.log10(rms)
                    else:
                        db = -60
                    
                    # Визуализация уровня
                    level_normalized = min(max((db + 60) / 60, 0), 1)
                    level_bars = int(level_normalized * 10)
                    level_meter = "█" * level_bars + "░" * (10 - level_bars)
                    
                    # Цвет индикатора в зависимости от уровня
                    if level_normalized > 0.9:
                        color = "#FF0000"
                    elif level_normalized > 0.7:
                        color = "#FF6600"
                    elif level_normalized > 0.5:
                        color = "#FFFF00"
                    else:
                        color = "#00FF00"
                    
                    self.level_meter.setText(level_meter)
                    self.level_meter.setStyleSheet(f"color: {color};")
                    self.level_db.setText(f"Уровень: {db:.1f} dB")
                
                # Воспроизводим
                self.output_stream.write(audio_final.tobytes())
                
                # Сбрасываем счетчик ошибок при успешной обработке
                error_count = 0
                
            except IOError as e:
                # Аудио ошибки - пропускаем и продолжаем
                error_count += 1
                print(f"Audio IO error #{error_count}: {e}")
                time.sleep(0.01)
                
            except Exception as e:
                # Другие ошибки
                error_count += 1
                print(f"Audio processing error #{error_count}: {e}")
                time.sleep(0.1)
        
        if error_count >= max_errors:
            print("Too many errors, stopping audio")
            self.stop_audio()
    
    def stop_audio(self):
        """Остановка аудио"""
        self.is_playing = False
        
        # Закрываем потоки
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
            self.input_stream = None
            
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
            self.output_stream = None
        
        # Обновляем UI
        self.start_btn.setText("🎵 Старт супер-усиление")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.status_label.setText("Готов к работе")
        self.status_label.setStyleSheet("color: black; font-weight: bold;")
        self.level_meter.setText("░░░░░░░░░░")
        self.level_db.setText("Уровень: -- dB")
    
    def test_audio(self):
        """Тест аудио системы"""
        try:
            output_index = self.output_combo.currentData()
            if output_index is None:
                QMessageBox.warning(self, "Ошибка", "Сначала выберите устройство вывода!")
                return
                
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                output_device_index=output_index
            )
            
            # Генерируем тестовый тон с большей амплитудой
            duration = 0.5
            samples = int(44100 * duration)
            t = np.linspace(0, duration, samples, False)
            
            # Генерируем несколько частот для лучшего теста
            tone1 = np.sin(2 * np.pi * 440 * t) * 0.7  # Ля
            tone2 = np.sin(2 * np.pi * 880 * t) * 0.3  # Ля на октаву выше
            tone = tone1 + tone2
            
            # Применяем усиление для теста
            tone_boosted = tone * 0.8  # 80% громкости
            
            audio_data = (tone_boosted * 32767).astype(np.int16).tobytes()
            
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            
            QMessageBox.information(self, "Тест", "Тестовый звук воспроизведен!")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка теста", f"Не удалось воспроизвести звук: {e}")
    
    def closeEvent(self, event):
        self.stop_audio()
        self.audio.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioBridgeEnhanced()
    window.show()
    sys.exit(app.exec_())