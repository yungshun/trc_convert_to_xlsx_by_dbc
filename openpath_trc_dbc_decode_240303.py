from PyQt6 import QtWidgets, QtCore
import sys
import os
import can
import pandas as pd
import cantools
import canmatrix
'''
def is_multiplexer_in_message(db, can_id):
    message = db.get_message_by_frame_id(can_id)
    if message:
        for signal in message.signals:
            if signal.is_multiplexer:
                return True
    return False
'''
class Worker(QtCore.QThread):
    update_signal = QtCore.pyqtSignal(str)
    finished_signal = QtCore.pyqtSignal()

    def __init__(self, trc_path, dbc_path,trc_name):
        super().__init__()
        self.trc_path = trc_path
        self.dbc_path = dbc_path
        self.trc_name = trc_name
        self.ID_list = []
        self.dbc_dic = {}
        self.dbc_key = []
        self.c = []

        db = cantools.database.load_file(dbc_path)
        dbc_dic = {}
        dbc_dic_list = []
        
        offset = 1
        x = ['Num','TimpStamp','Ch','Type','CAN-ID','Dash','DLC','Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7','Decode']# normal PCAN log formation, Decode is for DBC 
        
        for message in db.messages:
            self.ID_list.append(message.frame_id)
            for signal in message.signals:
                dbc_dic[signal.name] = offset
                #print(signal.name)
                dbc_dic_list.append(signal.name)
                x.append(signal.name)
                offset = offset + 1

        self.dbc_dic = dbc_dic
        self.dbc_key = dbc_dic_list
        self.c = x
        #
        # print(offset)
    def run(self):
        trc_path = self.trc_path
        dbc_path = self.dbc_path
        trc_file = trc_path
        db = cantools.database.load_file(dbc_path)
        
        CAN_ID_list = self.ID_list  # You need to obtain the CAN_ID_list here

        can_messages = []
        can2_messages = []
        c = ['Num','TimpStamp','Ch','Type','CAN-ID','Dash','DLC','Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7','Decode']# normal PCAN log formation, Decode is for DBC 
        #c = []
        c1 = ['Num','TimpStamp','Ch','Type','CAN-ID','Dash','DLC','Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7']
        for item in self.dbc_key:
            c1.append(item)
        #print(c1,'hahah')
        #print(len(c1),'len')
        #x = self.c
        #print(x)
        x = [0    ,1          ,2   ,3     ,4       ,5     ,6    ,7      ,8      ,9      ,10     ,11     ,12     ,13     ,14     ,15]

        #print(self.dbc_dic)
        try:     
            i = 0
            with open(trc_file, 'r') as trc_file:
                #print(trc_file)
                for line in trc_file:
                    if line[0] != ';':
                        parts = []
                        line = line.strip()
                        parts = line.split()
                        DLC = int(parts[6])
                        rawData = []
                        if DLC == 1:
                            rawData.append(parts[7])
                        if DLC == 2:
                            rawData = parts[7:9]
                        if DLC == 3:
                            rawData = parts[7:10]
                        if DLC == 4:
                            rawData = parts[7:11]
                        if DLC == 5:
                            rawData = parts[7:12]
                        if DLC == 6:
                            rawData = parts[7:13]
                        if DLC == 7:
                            rawData = parts[7:14]
                        if DLC == 8:
                            rawData = parts[7:]
                        blank = 8 - DLC
                        for i in range(blank):
                            parts.append(None)
                        #print(parts)
                        CAN_ID = int(parts[4], 16)
                        final_index = 0
                        partstmp = []
                        partstmp.extend(parts)
                        if CAN_ID in CAN_ID_list:
                            try :
                                decimal_integers = [int(hex_string, 16) for hex_string in rawData]
                                decode_result = db.decode_message(CAN_ID, decimal_integers)
                                item_list = []
                                item_list = [(key, value) for key, value in decode_result.items()]
                                parts.append(item_list)
                                #print(partstmp)
                                #print(decode_result.items())
                                start_index = 1
                                for key, value in decode_result.items():
                                    final_index = value_index = self.dbc_dic[key]
                                    for i in range(start_index,value_index + 1):
                                        if i == value_index:
                                            if value == None:
                                                partstmp.append(None) 
                                                print('nA')
                                                #print(None) 
                                                pass                                    
                                            else:   
                                                partstmp.append(value) 
                                                #print(value)
                                        else:
                                           partstmp.append(None) 
                                        start_index = final_index+1
                                #print(partstmp)
                            except:
                                #print('fail',final_index)
                                #parts.append(None)
                                pass
                        else:
                            #parts.append(None)
                            pass

                        
                        if final_index < len(self.dbc_dic):
                            #print(final_index,len(self.dbc_dic))
                            for i in range(final_index,len(self.dbc_dic)):
                                #print(partstmp)
                                partstmp.append(None)

                        #print(partstmp)
                        can_messages.append(parts)
                        can2_messages.append(partstmp)
                        '''
                        if len(partstmp)!=len(c1):
                            print(len(partstmp),len(c1))
                        else:
                            print('ok')
                        '''
                    i = i+ 1
                    self.update_signal.emit("Processing"+'.'* i)
            self.update_signal.emit("Saving"+'.'* i)
            df = pd.DataFrame(can_messages, columns=c)
            filename = self.trc_name + ".xlsx"  # Update this as needed
            df.to_excel(filename,index=False)

            df1 = pd.DataFrame(can2_messages, columns=c1)
            filename = self.trc_name + '_decode' + ".xlsx"


            columns_to_remove = [col for col in df1.columns if all(df1[col].isna())]

            # Remove identified columns
            df_cleaned = df1.drop(columns=columns_to_remove)

            df_cleaned.to_excel(filename,index=False)

            self.finished_signal.emit()  # Signal that processing is complete
        except Exception as e:
            print(f"Error during processing: {e}")

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('trc_decode')
        self.resize(600, 600)
        self.ui()
        self.trc_file_path = None
        self.dbc_file_path = None
        self.trc_name = None

    def ui(self):
        self.btn1 = QtWidgets.QPushButton(self)
        self.btn1.move(20, 20)
        self.btn1.setText('select .trc file')
        self.btn1.clicked.connect(self.openTrcFile)

        self.btn2 = QtWidgets.QPushButton(self)
        self.btn2.move(20, 100)
        self.btn2.setText('select .dbc file')
        self.btn2.clicked.connect(self.openDbcFile)

        self.file_path_input = QtWidgets.QLineEdit(self)
        self.file_path_input.setGeometry(20, 60, 500, 30)

        self.file_path_input1 = QtWidgets.QLineEdit(self)
        self.file_path_input1.setGeometry(20, 140, 500, 30)

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(20, 180, 100, 20)

        self.btn = QtWidgets.QPushButton(self)
        self.btn.setText('convert')
        self.btn.setGeometry(20, 220, 100, 30)
        self.btn.clicked.connect(self.CAN_Decode)

    def openTrcFile(self):
        trc_file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(filter='TRC Files (*.trc);;All Files (*)')

        if trc_file_paths:
            self.trc_file_path = trc_file_paths[0]
            self.file_path_input.setText(self.trc_file_path)
            #self.file_names =
                            
        for filePath in trc_file_paths:
            file_name_with_extension = os.path.basename(filePath)
            file_name, file_extension = os.path.splitext(file_name_with_extension)
            self.trc_name = file_name
           # print(file_name)


    def openDbcFile(self):
        dbc_file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(filter='DBC Files (*.dbc);;All Files (*)')

        if dbc_file_paths:
            self.dbc_file_path = dbc_file_paths[0]
            self.file_path_input1.setText(self.dbc_file_path)

    def CAN_Decode(self):
        trc_path = self.file_path_input.text()
        dbc_path = self.file_path_input1.text()
        trc_name = self.trc_name

        if not trc_path or not dbc_path:
            self.label.setText("Error: Please select both .trc and .dbc files.")
            return

        self.label.setText("Processing...")

        # Start the worker thread
        self.worker = Worker(trc_path, dbc_path,trc_name)
        self.worker.update_signal.connect(self.update_progress_label)
        self.worker.finished_signal.connect(self.processing_finished)
        self.worker.start()

    def update_progress_label(self, text):
        self.label.setText(text)
        
    def processing_finished(self):
        self.label.setText("Finish")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Form = MyWidget()
    Form.show()
    sys.exit(app.exec())
