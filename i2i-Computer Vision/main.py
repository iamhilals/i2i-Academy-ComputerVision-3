import cv2
import mediapipe as mp 
import cvzone 
import math
import numpy as np
import comtypes
from ctypes import cast, POINTER
from pycaw.pycaw import IAudioEndpointVolume, IMMDeviceEnumerator

#ses bağlantısı ayarları
CLSID_MMDeviceEnumerator = comtypes.GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
device_enumerator = comtypes.CoCreateInstance(
    CLSID_MMDeviceEnumerator,
    IMMDeviceEnumerator,
    comtypes.CLSCTX_ALL
)
endpoint = device_enumerator.GetDefaultAudioEndpoint(0, 1)
interface = endpoint.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

#kamera kısmı
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)


img_bozkurt = cv2.imread("bozkurt.png", cv2.IMREAD_UNCHANGED) 
img_bozkurt = cv2.resize(img_bozkurt, (150, 150)) 

#mediapipe 
mp_hands = mp.solutions.hands
hand_dedector = mp_hands.Hands(max_num_hands=2) 
mp_drawing = mp.solutions.drawing_utils
parmak_uclari = [8, 12, 16, 20] 


while True:
    basarili_mi, kare = camera.read()
    
    if not basarili_mi: 
        continue
        
    rgb_kare = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
    result = hand_dedector.process(rgb_kare)
    
    if result.multi_hand_landmarks:
        for el_bilgisi, el_landmarks in zip(result.multi_handedness, result.multi_hand_landmarks):
            mp_drawing.draw_landmarks(kare, el_landmarks, mp_hands.HAND_CONNECTIONS) # İskeleti ekrana çizdirme
            
            el_tarafi = el_bilgisi.classification[0].label
            koordinat_list = []
            
            for id, landmark in enumerate(el_landmarks.landmark):
                height, weight, kanal = kare.shape
                x_koordinat = int(landmark.x * weight)
                y_koordinat = int(landmark.y * height)
                koordinat_list.append([id, x_koordinat, y_koordinat])
                
            
            anlik_parmaklar = []
            
            
            if el_tarafi == "Right":
                if koordinat_list[4][1] < koordinat_list[2][1]:  #başparmak
                    anlik_parmaklar.append(1) # Açık
                else:
                    anlik_parmaklar.append(0) # Kapalı
            else:
                if koordinat_list[4][1] > koordinat_list[2][1]: 
                    anlik_parmaklar.append(1)
                else:
                    anlik_parmaklar.append(0)
                    
            for uc_noktasi in parmak_uclari:
                if koordinat_list[uc_noktasi][2] < koordinat_list[uc_noktasi - 3][2]:
                    anlik_parmaklar.append(1) 
                else:
                    anlik_parmaklar.append(0) 
                    
            
            acik_parmak_sayisi = sum(anlik_parmaklar)
            cv2.putText(kare, f"Parmak: {acik_parmak_sayisi}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)            
                    
           
            if anlik_parmaklar == [0, 1, 0, 0, 1]:
                kare = cvzone.overlayPNG(kare, img_bozkurt, [50, 50])
                
           #ses kısmı için parmak durumunu kotnrol etme 
            if len(anlik_parmaklar) >= 5 and anlik_parmaklar[2] == 0 and anlik_parmaklar[3] == 0 and anlik_parmaklar[4] == 0:
                
                 
                x1, y1 = koordinat_list[4][1], koordinat_list[4][2] # başparmak-> 4
                x2, y2 = koordinat_list[8][1], koordinat_list[8][2] # işaret Parmağı-> 8


                cv2.line(kare, (x1, y1), (x2, y2), (0, 255, 0), 3) # Parmaklar arası çizgi
                
                # mesafeyi ölç ve sesi ayarla
                mesafe = int(math.hypot(x2 - x1, y2 - y1))
                ses_seviyesi = np.interp(mesafe, [23, 230], [-65, 0])
                volume.SetMasterVolumeLevel(ses_seviyesi, None)
                
                
                cv2.putText(kare, f"Mesafe: {mesafe}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3) # ekrana mesafe bilgisini yazdır
            else:
                cv2.putText(kare, "Ses Kilidi Kapali", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3) # kilit kapalıysa ekrana kırmızı renkle uyarı yazısı yazdır
                
    # Görüntüyü yansıt
    cv2.imshow("Kamera", kare)
    
    # 'q' tuşuna basılırsa döngüden çık
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()