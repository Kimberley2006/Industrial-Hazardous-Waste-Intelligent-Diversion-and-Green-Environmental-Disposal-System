import cv2
import numpy as np
import serial
import time

# ------------------- 参数配置 -------------------
SERIAL_PORT = 'COM3'  # 工控机与PLC通信串口号
BAUD_RATE = 9600
MIN_AREA = 500         # 最小有效面积(像素²)
# 分类阈值 (需根据实际样本校准)
THRESH_ALUMINUM_AREA = 5000
THRESH_ALUMINUM_RATIO = 3.0
THRESH_STAINLESS_COMPLEX = 0.3
THRESH_CARBON_AREA = 2000

# ------------------- 初始化 -------------------
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
cap = cv2.VideoCapture(0)  # 0为工业相机索引号

def classify_waste(contour):
    """核心分类判定函数"""
    # 1. 计算投影面积
    area = cv2.contourArea(contour)
    if area < MIN_AREA:
        return None
    
    # 2. 计算长宽比
    rect = cv2.minAreaRect(contour)
    w, h = rect[1]
    ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1.0
    
    # 3. 计算轮廓复杂度(圆形度)
    perimeter = cv2.arcLength(contour, True)
    complexity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 1.0
    
    # 4. 多特征规则判定
    if area > THRESH_ALUMINUM_AREA and ratio > THRESH_ALUMINUM_RATIO:
        return 'Aluminum'
    elif THRESH_CARBON_AREA < area <= THRESH_ALUMINUM_AREA and complexity < THRESH_STAINLESS_COMPLEX:
        return 'Stainless'
    elif area <= THRESH_CARBON_AREA and ratio < THRESH_ALUMINUM_RATIO:
        return 'Carbon'
    else:
        return 'Abnormal'

# ------------------- 主循环 -------------------
print("视觉系统启动...")
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # 1. 图像预处理
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # 2. 轮廓提取
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 3. 分类判定与通信
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        result = classify_waste(largest_contour)
        
        if result:
            print(f"识别结果: {result}")
            # 发送结果给PLC (简单协议: 开头'A'+'S'+'C'+'A'+'\n')
            ser.write(f"{result}\n".encode())
            
            # 可视化绘制
            cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
            cv2.putText(frame, result, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow('Vision System', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
ser.close()