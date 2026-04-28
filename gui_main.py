import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QGroupBox)
from PyQt5.QtCore import QTimer, Qt
import minimalmodbus

class WasteMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工业边角料智能分流系统 - 上位机监控")
        self.setGeometry(100, 100, 800, 600)
        
        # Modbus连接 (连接PLC)
        try:
            self.instrument = minimalmodbus.Instrument('COM4', 1) # 串口地址, PLC站号
            self.instrument.serial.baudrate = 9600
            self.instrument.serial.timeout = 0.5
        except Exception as e:
            print(f"Modbus连接失败: {e}")

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000) # 1秒刷新一次

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 1. 系统状态组
        self.status_group = QGroupBox("系统运行状态")
        status_layout = QVBoxLayout()
        self.lbl_system = QLabel("系统状态: 待机")
        self.lbl_aluminum = QLabel("铝合金数量: 0")
        self.lbl_stainless = QLabel("不锈钢数量: 0")
        self.lbl_carbon = QLabel("碳钢数量: 0")
        status_layout.addWidget(self.lbl_system)
        status_layout.addWidget(self.lbl_aluminum)
        status_layout.addWidget(self.lbl_stainless)
        status_layout.addWidget(self.lbl_carbon)
        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)

        # 2. 报警日志
        self.log_group = QGroupBox("报警日志")
        log_layout = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        self.log_group.setLayout(log_layout)
        layout.addWidget(self.log_group)

        # 3. 控制按钮
        self.btn_start = QPushButton("启动系统")
        self.btn_stop = QPushButton("停止系统")
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)

    def update_data(self):
        """定时从PLC读取数据"""
        try:
            # 假设从PLC寄存器读取数量 (地址40001, 40002, 40003)
            count_al = self.instrument.read_register(0, 0) 
            count_ss = self.instrument.read_register(1, 0)
            count_c = self.instrument.read_register(2, 0)
            
            self.lbl_aluminum.setText(f"铝合金数量: {count_al}")
            self.lbl_stainless.setText(f"不锈钢数量: {count_ss}")
            self.lbl_carbon.setText(f"碳钢数量: {count_c}")
            self.lbl_system.setText("系统状态: 运行中")
            self.lbl_system.setStyleSheet("color: green;")
            
        except Exception as e:
            self.txt_log.append(f"通信异常: {str(e)}")
            self.lbl_system.setText("系统状态: 通信中断")
            self.lbl_system.setStyleSheet("color: red;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WasteMonitorApp()
    window.show()
    sys.exit(app.exec_())