import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QSlider, QLabel, QWidget, 
                             QPushButton, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyaudio
import threading
import time

class AudioBridgeFixed(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.is_playing = False
        self.boost_level = 1.0
        self.input_stream = None
        self.output_stream = None
        
        self.init_ui()
        self.scan_audio_devices()
        
    def init_ui(self):
        self.setWindowTitle("Audio Bridge Fixed - Усилитель системного звука")
        self.setFixedSize(600, 400)
        
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
        
        # Управление усилением
        layout.addWidget(QLabel("Уровень усиления:"))
        
        self.boost_slider = QSlider(Qt.Horizontal)
        self.boost_slider.setMinimum(100)
        self.boost_slider.setMaximum(10000)
        self.boost_slider.setValue(100)
        self.boost_slider.valueChanged.connect(self.update_boost)
        layout.addWidget(self.boost_slider)
        
        self.boost_label = QLabel("100%")
        self.boost_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.boost_label)
        
        # Индикатор уровня
        self.level_label = QLabel("Уровень сигнала: --")
        layout.addWidget(self.level_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🎵 Старт усиление")
        self.start_btn.clicked.connect(self.toggle_audio)
        button_layout.addWidget(self.start_btn)
        
        refresh_btn = QPushButton("🔄 Обновить устройства")
        refresh_btn.clicked.connect(self.scan_audio_devices)
        button_layout.addWidget(refresh_btn)
        
        test_btn = QPushButton("🔊 Тест звука")
        test_btn.clicked.connect(self.test_audio)
        button_layout.addWidget(test_btn)
        
        layout.addLayout(button_layout)
        
        # Инструкция
        info = QLabel(
            "Инструкция:\n"
            "1. Выберите 'CABLE Output' как устройство захвата\n"
            "2. Выберите ваши колонки как устройство вывода\n" 
            "3. В настройках звука Windows установите 'CABLE Input' как устройство по умолчанию\n"
            "4. Нажмите 'Старт усиление' и запустите музыку"
        )
        info.setStyleSheet("background-color: #F0F8FF; padding: 10px; font-size: 10px;")
        layout.addWidget(info)
        
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
        
    def update_boost(self, value):
        self.boost_level = value / 100.0
        self.boost_label.setText(f"{value}%")
    
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
            self.status_label.setText("🎵 Усиление активно!")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Запускаем поток обработки
            self.audio_thread = threading.Thread(target=self.audio_processing_loop)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить аудио:\n{str(e)}")
    
    def audio_processing_loop(self):
        """Цикл обработки аудио с улучшенной обработкой ошибок"""
        error_count = 0
        max_errors = 5
        
        while self.is_playing and error_count < max_errors:
            try:
                # Читаем данные
                data = self.input_stream.read(1024, exception_on_overflow=False)
                
                # Рассчитываем уровень сигнала
                audio_array = np.frombuffer(data, dtype=np.int16)
                if len(audio_array) > 0:
                    rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2))
                    level = min(int(rms / 1000), 10)
                    level_bars = "█" * level + "░" * (10 - level)
                    self.level_label.setText(f"Уровень: {level_bars}")
                
                # Применяем усиление
                boosted_audio = audio_array.astype(np.float32) * self.boost_level
                boosted_audio = np.clip(boosted_audio, -32767, 32767)
                
                # Воспроизводим
                self.output_stream.write(boosted_audio.astype(np.int16).tobytes())
                
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
        self.start_btn.setText("🎵 Старт усиление")
        self.status_label.setText("Готов к работе")
        self.status_label.setStyleSheet("color: black; font-weight: bold;")
        self.level_label.setText("Уровень сигнала: --")
    
    def test_audio(self):
        """Тест аудио системы"""
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True
            )
            
            # Генерируем тестовый тон
            duration = 0.3
            samples = int(44100 * duration)
            t = np.linspace(0, duration, samples, False)
            tone = np.sin(2 * np.pi * 440 * t) * 0.5 * 32767
            audio_data = tone.astype(np.int16).tobytes()
            
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
    window = AudioBridgeFixed()
    window.show()
    sys.exit(app.exec_())