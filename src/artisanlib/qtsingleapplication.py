'''
Source: https://github.com/IARI/alsa_jack_gui
Author: https://github.com/IARI
Original Source: http://stackoverflow.com/questions/12712360/qtsingleapplication-for-pyside-or-pyqt
Original Author: user763305
Notes: Modified for PyQt5; further modified to remove blocking sockets remaining from died server
'''

from PyQt5.QtCore import pyqtSignal, QTextStream, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalSocket, QLocalServer


class QtSingleApplication(QApplication):
    messageReceived = pyqtSignal(str)

    def __init__(self, id, *argv):

        super(QtSingleApplication, self).__init__(*argv)
        self._id = id
        self._activationWindow = None
        self._activateOnMessage = False

        # Is there another instance running?
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._id)
        self._isRunning = self._outSocket.waitForConnected(-1)

        if self._isRunning:
            # Yes, there is.
            self._outStream = QTextStream(self._outSocket)
            self._outStream.setCodec('UTF-8')
        else:
            # No, there isn't.
            # First we remove existing servers of that name that might not have been properly closed as the server died
            QLocalServer.removeServer(self._id) 
            self._outSocket = None
            self._outStream = None
            self._inSocket = None
            self._inStream = None
            self._server = QLocalServer()
            self._server.listen(self._id)
            self._server.newConnection.connect(self._onNewConnection)

    def isRunning(self):
        return self._isRunning

    def id(self):
        return self._id

    def activationWindow(self):
        return self._activationWindow

    def setActivationWindow(self, activationWindow, activateOnMessage=True):
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self):
        if not self._activationWindow:
            return

        self._activationWindow.show()
        self._activationWindow.setWindowState(
            self._activationWindow.windowState() & ~Qt.WindowMinimized)
        self._activationWindow.raise_()
        self._activationWindow.activateWindow()

    def sendMessage(self, msg):
        if not self._outStream:
            return False
        self._outStream << msg << '\n'
        self._outStream.flush()
        return self._outSocket.waitForBytesWritten()

    def _onNewConnection(self):
        if self._inSocket:
            self._inSocket.readyRead.disconnect(self._onReadyRead)
        self._inSocket = self._server.nextPendingConnection()
        if not self._inSocket:
            return
        self._inStream = QTextStream(self._inSocket)
        self._inStream.setCodec('UTF-8')
        self._inSocket.readyRead.connect(self._onReadyRead)
#        if self._activateOnMessage:
#            self.activateWindow()

    def _onReadyRead(self):
        while True:
            msg = self._inStream.readLine()
            if not msg: break
            self.messageReceived.emit(msg)
