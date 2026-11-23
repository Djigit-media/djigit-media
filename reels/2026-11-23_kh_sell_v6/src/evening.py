# Подгонка цвета фото под тёплую закатную серию p (перенос статистик цвета в LAB, как color match в монтаже)
import numpy as np, cv2, sys
from PIL import Image
B_='/home/claude/djigit-media/reels/2026-11-22_kh_sell/ph/'
REF = [B_ + 'p4.png', B_ + 'p7.png', B_ + 'n1.png', B_ + 'p10_fix.png']
def lab(p):
    return cv2.cvtColor(np.array(Image.open(p).convert('RGB')), cv2.COLOR_RGB2LAB).astype(np.float32)
def stats(L): return L.reshape(-1, 3).mean(0), L.reshape(-1, 3).std(0)
R = [stats(lab(p)) for p in REF]; RM = np.mean([r[0] for r in R], 0); RS = np.mean([r[1] for r in R], 0)
def evening(src, dst, amt=0.9):
    L = lab(src); m, s = stats(L)
    T = (L - m) / s * RS + RM
    T = L * (1 - amt) + T * amt
    rgb = cv2.cvtColor(np.clip(T, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255
    h, w = rgb.shape[:2]; X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
    rgb = rgb * (1 - .22 * np.clip(X ** 2 + Y ** 2 - .4, 0, 1))[..., None]
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(dst)
if __name__ == '__main__':
    evening(sys.argv[1], sys.argv[2])
