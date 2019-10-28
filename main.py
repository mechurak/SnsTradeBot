import sys
from PyQt5.QtWidgets import QApplication
from ui.MainWindow import MainWindow
from util.logger import MyLogger

if __name__ == "__main__":
    MyLogger.instance().logger().info("===== Start SnsTradeBot ======")
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
