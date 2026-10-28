# Phan tich ECG 30 giay (250 mau/giay): loc nhieu 50 Hz va troi nen, tim dinh R, tinh nhip tim.
# Cung thuat toan voi app/suc_khoe/lib/ecg.dart (Pan-Tompkins rut gon):
#   1. Trung binh 5 mau (20 ms) -> triet nhieu dien luoi 50 Hz.
#   2. Tru trung binh 0,6 giay -> bo troi nen (tho, cu dong).
#   3. Dao ham, binh phuong, tich phan cua so 150 ms -> nang luong phuc bo QRS.
#   4. Nguong = 0,3 x phan vi 98 %; moi vung vuot nguong lay 1 dinh, cach nhau >= 250 ms.
#   5. Nhip tim = 60 / trung vi khoang R-R (bo khoang ngoai 0,3-2 giay).
# Chay: python phan_tich_ecg.py            -> thu voi song gia (45-150 lan/phut, ca khi dao cuc)
#       python phan_tich_ecg.py file.csv   -> phan tich file CSV tu firmware/doc_ad8232 (cot ecg)
import csv, sys
import math, random
FS=250
def tbtruot(x, w):
    # trung binh truot can giua, cua so w (le), bien: thu nho cua so
    n=len(x); h=w//2; p=[0.0]
    for v in x: p.append(p[-1]+v)
    out=[]
    for i in range(n):
        a=max(0,i-h); b=min(n,i+h+1)
        out.append((p[b]-p[a])/(b-a))
    return out
def loc(x):
    s=tbtruot(x,5)
    b=tbtruot(s,151)
    return [s[i]-b[i] for i in range(len(x))]
def tim_r(y):
    n=len(y)
    d=[0.0]*n
    for i in range(2,n-2): d[i]=y[i+2]-y[i-2]
    m=tbtruot([v*v for v in d],37)
    bo=FS//2
    giua=sorted(m[bo:n-bo]) if n>2*bo+10 else sorted(m)
    if not giua: return []
    p=giua[int(0.98*(len(giua)-1))]
    thr=0.3*p
    if p<=0: return []
    dinh=[]
    i=0
    while i<n:
        if m[i]>thr:
            j=i; best=i
            while j<n and m[j]>thr:
                if m[j]>m[best]: best=j
                j+=1
            # vi tri R: |y| lon nhat quanh dinh m
            a=max(0,best-FS//10); b=min(n,best+FS//10)
            r=max(range(a,b), key=lambda k: abs(y[k]))
            if dinh and r-dinh[-1] < FS*0.25:
                if abs(y[r])>abs(y[dinh[-1]]): dinh[-1]=r
            else:
                dinh.append(r)
            i=j
        else: i+=1
    return dinh
def nhip(dinh):
    rr=[(dinh[i+1]-dinh[i])/FS for i in range(len(dinh)-1)]
    rr=[v for v in rr if 0.3<=v<=2.0]
    if len(rr)<2: return None
    rr.sort(); med=rr[len(rr)//2]
    return 60/med
def tao(bpm=72, giay=30, nhieu=True, dao=False, seed=1):
    random.seed(seed)
    n=giay*FS; x=[]
    T=60/bpm
    for i in range(n):
        t=i/FS; ph=(t%T)
        v=0
        v+= 0.12*math.exp(-((ph-0.15)/0.03)**2)    # P
        v+= -0.1*math.exp(-((ph-0.26)/0.008)**2)   # Q
        v+= 1.0*math.exp(-((ph-0.28)/0.01)**2)     # R
        v+= -0.25*math.exp(-((ph-0.30)/0.01)**2)   # S
        v+= 0.3*math.exp(-((ph-0.5)/0.05)**2)      # T
        if dao: v=-v
        if nhieu:
            v+= 0.6*math.sin(2*math.pi*0.3*t) + 0.15*math.sin(2*math.pi*50*t) + random.gauss(0,0.04)
        x.append(int(1900+300*v))
    return x
if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], newline='') as f:
            x = [int(r['ecg']) for r in csv.DictReader(r for r in f if not r.startswith('#'))]
        d = tim_r(loc(x))
        print(f'{len(x)} mau, {len(d)} dinh R, nhip tim {nhip(d) or 0:.0f} lan/phut')
    else:
        for bpm in (45, 72, 110, 150):
            for dao in (False, True):
                x = tao(bpm, dao=dao); d = tim_r(loc(x)); h = nhip(d) or 0
                print(f'song gia {bpm:3d} lan/phut{" (dao cuc)" if dao else ""}: tim {len(d)} dinh, nhip {h:.1f}')
