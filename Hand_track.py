

import cv2
import mediapipe as mp
import time



# hand work

class DetectorRuk:
    """
    відстеження рук на відео
    Знаходить руки, показує точки на них, і може визначити які пальці підняті
    """

    def __init__(self, skilky_ruk=2, min_vpevnenist=0.7):
        """
        Налаштування детектора

        skilky_ruk - скільки максимум рук шукати (1 або 2)
        min_vpevnenist - наскільки впевнено шукати руки (0.7 = 70% впевненості)
        """

        # Підключаємо інструменти MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        # Створюємо детектор рук з нашими налаштуваннями
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,  # False = відео режим (швидше)
            max_num_hands=skilky_ruk,  # скільки рук шукати
            min_detection_confidence=min_vpevnenist,  # впевненість пошуку
            min_tracking_confidence=min_vpevnenist  # впевненість слідкування
        )

        # Номери кінчиків пальців (з 21 точки на руці)
        # 4-великий, 8-вказівний, 12-середній, 16-безіменний, 20-мізинець
        self.kintsi_paltsiv = [4, 8, 12, 16, 20]

        # Тут будемо зберігати координати точок
        self.koordinaty = []

        # Тут зберігаємо яка рука (права чи ліва)
        self.yaka_ruka = ""

    def znayty_ruky(self, kartynka, malyuvaty=True):
        """
        Знаходить руки на картинці

        kartynka - кадр з камери
        malyuvaty - чи малювати точки на руках (True/False)
        """

        # MediaPipe працює з RGB, а камера дає BGR - треба перетворити
        kartynka_rgb = cv2.cvtColor(kartynka, cv2.COLOR_BGR2RGB)

        # Шукаємо руки!
        self.rezultaty = self.hands.process(kartynka_rgb)

        # Якщо знайшли хоч одну руку
        if self.rezultaty.multi_hand_landmarks:

            # Для кожної знайденої руки
            for ruka in self.rezultaty.multi_hand_landmarks:

                # Якщо треба малювати - малюємо точки і з'єднання
                if malyuvaty:
                    self.mp_draw.draw_landmarks(
                        kartynka,  # де малювати
                        ruka,  # що малювати (точки руки)
                        self.mp_hands.HAND_CONNECTIONS  # з'єднання між точками
                    )

        return kartynka

    def otrymaty_koordinaty(self, kartynka, nomer_ruky=0):
        """
        Отримує координати всіх 21 точок руки

        kartynka - кадр з камери
        nomer_ruky - яку руку брати (0=перша, 1=друга)

        Повертає список: [[id, x, y], [id, x, y], ...]
        """

        self.koordinaty = []  # очищаємо старі дані

        # Якщо руки знайдено
        if self.rezultaty.multi_hand_landmarks:

            # Вибираємо потрібну руку
            moya_ruka = self.rezultaty.multi_hand_landmarks[nomer_ruky]

            # Визначаємо права чи ліва рука
            info_pro_ruku = self.rezultaty.multi_handedness[nomer_ruky]
            self.yaka_ruka = info_pro_ruku.classification[0].label  # "Right" або "Left"

            # Розмір картинки (для перетворення координат)
            vysota, shyryna, _ = kartynka.shape

            # Проходимо по всіх 21 точках руки
            for id_tochky, tochka in enumerate(moya_ruka.landmark):
                # Перетворюємо координати з 0-1 в пікселі
                x = int(tochka.x * shyryna)
                y = int(tochka.y * vysota)

                # Додаємо в список [номер точки, x, y]
                self.koordinaty.append([id_tochky, x, y])

        return self.koordinaty

    def yaki_paltsi_pidnyato(self):
        """
        Визначає які пальці підняті

        Повертає список з 5 чисел:
        [1, 0, 1, 0, 0] означає підняті великий і середній пальці
        1 = палець підняти, 0 = палець опущений
        """

        paltsi = []  # тут зберігатимемо результат

        # Якщо координат немає - повертаємо пусто
        if len(self.koordinaty) == 0:
            return []

        # ============ ВЕЛИКИЙ ПАЛЕЦЬ (особливий) ============
        # Порівнюємо кінчик (4) з основою (2)
        kinchyk_x = self.koordinaty[4][1]  # x координата кінчика
        osnova_x = self.koordinaty[2][1]  # x координата основи

        # Логіка залежить від того, яка рука
        if self.yaka_ruka == "Right":
            # Для правої руки: якщо кінчик ЛІВІШЕ основи = підняти
            if kinchyk_x < osnova_x:
                paltsi.append(1)
            else:
                paltsi.append(0)
        else:  # Left
            # Для лівої руки: якщо кінчик ПРАВІШЕ основи = підняти
            if kinchyk_x > osnova_x:
                paltsi.append(1)
            else:
                paltsi.append(0)

        # ============ ІНШІ 4 ПАЛЬЦІ ============
        # Порівнюємо кінчик з точкою на 2 позиції нижче
        for i in range(1, 5):
            nomer_kinchyka = self.kintsi_paltsiv[i]  # номер кінчика (8, 12, 16, 20)

            kinchyk_y = self.koordinaty[nomer_kinchyka][2]  # y кінчика
            seryna_y = self.koordinaty[nomer_kinchyka - 2][2]  # y середини

            # Якщо кінчик ВИЩЕ середини = палець підняти
            if kinchyk_y < seryna_y:
                paltsi.append(1)
            else:
                paltsi.append(0)

        return paltsi


# ========================================
# ГОЛОВНА ПРОГРАМА
# ========================================
def main():
    """
    Основна програма - відкриває камеру і показує результат
    """

    # Змінні для підрахунку FPS (кадрів за секунду)
    chas_poperedni = 0
    chas_teraz = 0

    # Відкриваємо камеру (0 = вбудована камера)
    kamera = cv2.VideoCapture(0)

    # Перевіряємо чи камера працює
    if not kamera.isOpened():
        print("❌ Помилка: не можу відкрити камеру!")
        return

    # Створюємо наш детектор рук
    detektor = DetectorRuk(skilky_ruk=2, min_vpevnenist=0.7)

    print("✅ Програма запущена! Натисніть 'q' щоб вийти")

    # Головний цикл програми
    while True:

        # Читаємо кадр з камери
        uspishno, kadr = kamera.read()

        # Якщо не вдалося прочитати - виходимо
        if not uspishno:
            print("❌ Не можу прочитати кадр з камери")
            break

        # Дзеркально відображаємо (щоб було зручніше)
        kadr = cv2.flip(kadr, 1)

        # 1) Знаходимо руки і малюємо на них точки
        kadr = detektor.znayty_ruky(kadr, malyuvaty=True)

        # 2) Отримуємо координати точок першої руки
        koordinaty = detektor.otrymaty_koordinaty(kadr, nomer_ruky=0)

        # 3) Визначаємо підняті пальці
        if len(koordinaty) > 0:
            paltsi = detektor.yaki_paltsi_pidnyato()

            # Рахуємо скільки пальців підняті
            skilky_pidnyato = paltsi.count(1)

            # Показуємо інформацію на екрані
            tekst = f"Ruka: {detektor.yaka_ruka} | Paltsi: {skilky_pidnyato}"
            cv2.putText(kadr, tekst, (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Показуємо стан кожного пальця
            nazvy = ["Velykyi", "Vkazivnyi", "Serednii", "Bezymennyi", "Mizinets"]
            for i, nazva in enumerate(nazvy):
                stan = "UP" if paltsi[i] == 1 else "DOWN"
                kolir = (0, 255, 0) if paltsi[i] == 1 else (0, 0, 255)
                cv2.putText(kadr, f"{nazva}: {stan}", (10, 140 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, kolir, 2)

        # Підраховуємо і показуємо FPS
        chas_teraz = time.time()
        fps = 1 / (chas_teraz - chas_poperedni)
        chas_poperedni = chas_teraz

        cv2.putText(kadr, f"FPS: {int(fps)}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        # Показуємо результат
        cv2.imshow('Vidstezhennya Ruk', kadr)

        # Якщо натиснули 'q' - виходимо
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Вихід з програми...")
            break

    # Закриваємо все
    kamera.release()
    cv2.destroyAllWindows()


# Запускаємо програму
if __name__ == "__main__":
    main()
