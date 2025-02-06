import machine
import time
import struct
import array
import os
# I2S Pinleri
BCLK_PIN = 11 # Bit Clock (BCLK) pin
LRCL_PIN = 12 # Word Select (LRCL) pin
DIN_PIN = 10 # Data In (DIN) pin
# WAV Başlık Bilgilerini Okuma
def read_wav_header(filename):
 with open(filename, 'rb') as f:
 header = f.read(44) # WAV header (ilk 44 byte)
 
 # WAV header'dan örnekleme hızını al
 sample_rate = struct.unpack('<I', header[24:28])[0]
 channels = struct.unpack('<H', header[22:24])[0]
 bits_per_sample = struct.unpack('<H', header[34:36])[0]
 
 print("Örnekleme Hızı:", sample_rate)
 print("Kanal Sayısı:", channels)
 print("Bit Derinliği:", bits_per_sample)
 
 return sample_rate, channels, bits_per_sample
# I2S yapılandırması
def setup_i2s(sample_rate, channels):
 try:
 # Buffer boyutunu artırdık
 buffer_size = 8192
 if channels == 1:
 i2s = machine.I2S(0, sck=machine.Pin(BCLK_PIN), ws=machine.Pin(LRCL_PIN), 
sd=machine.Pin(DIN_PIN), mode=machine.I2S.TX, bits=16, format=machine.I2S.MONO, rate=sample_rate, 
ibuf=buffer_size)
 else:
 i2s = machine.I2S(0, sck=machine.Pin(BCLK_PIN), ws=machine.Pin(LRCL_PIN), 
sd=machine.Pin(DIN_PIN), mode=machine.I2S.TX, bits=16, format=machine.I2S.STEREO, rate=sample_rate, 
ibuf=buffer_size)
 
 print("I2S yapılandırması başarılı!")
 return i2s
 except Exception as e:
 print("I2S yapılandırma hatası:", e)
 return None
# WAV Dosyasını Okuma
def read_wav_data(filename, chunk_size=1024):
 with open(filename, 'rb') as f:
 header = f.read(44) # WAV header (ilk 44 byte)
 print("WAV header okundu.")
 
 while True:
 chunk = f.read(chunk_size)
 if len(chunk) < chunk_size:
 break
 yield chunk
# 8-bit PCM'den 16-bit PCM'e Dönüştürme
def convert_8bit_to_16bit(chunk):
 data = array.array('B', chunk) # 8-bit unsigned data
 converted = array.array('h') # 16-bit signed data
 for sample in data:
 normalized = (sample - 128) * 256 # 8-bit'ten 16-bit'e dönüştür
 converted.append(max(min(normalized, 32767), -32768)) # Clipping
 return bytes(converted)
# Müzik çalma fonksiyonu
def play_music():
 wav_file = '/audio.wav' # Pico'nun içindeki WAV dosyasının yolu
 sample_rate, channels, bits_per_sample = read_wav_header(wav_file)
 # I2S'yi doğru örnekleme hızı ve kanal sayısı ile yapılandır
 i2s = setup_i2s(sample_rate, channels)
 if i2s is None:
 print("I2S başlatılamadı. Kodu kontrol edin.")
 raise SystemExit("I2S başlatılamadı.")
 
 try:
 for chunk in read_wav_data(wav_file, chunk_size=2048): # 2048 byte'lık parçalarla oku
 if bits_per_sample == 8:
 chunk = convert_8bit_to_16bit(chunk) # 8-bit'i 16-bit'e dönüştür
 i2s.write(chunk) # Her bir parçayı I2S ile çal
 time.sleep(0.005) # Küçük bir bekleme süresi
 print(f"{wav_file} başarıyla çalındı.")
 except Exception as e:
 print("Ses çalma hatası:", e)
# Ses seviyesini okuma fonksiyonu
def get_sound_level():
 # ADC pinini GP26 (A0) olarak kullanıyoruz (doğru ADC pinini seçtik)
 mic_pin = machine.Pin(26) # GP26 kullanılıyor
 adc = machine.ADC(mic_pin)
 sound_value = adc.read_u16() # 16-bit okuma
 return sound_value
# Komut dinleme fonksiyonu
def listen_for_commands():
 print("Mikrofon dinlemesi başlatıldı...")
 threshold_start = 4000 # Başlat komutu için ses seviyesi eşiği
 threshold_stop = 2000 # Durdur komutu için ses seviyesi eşiği
 is_playing = False
 
 while True:
 sound_level = get_sound_level()
 print(f"Ses seviyesi: {sound_level}")
 
 # Ses seviyesine göre komut algıla
 if sound_level > threshold_start and not is_playing:
 print("Başlat komutu algılandı!")
 play_music()
 is_playing = True # Müzik çalmaya başladı
 
 elif sound_level < threshold_stop and is_playing:
 print("Durdur komutu algılandı!")
 is_playing = False # Müzik durdu
 time.sleep(0.1)
# Başlat
listen_for_commands()