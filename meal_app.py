import sys
import requests
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextBrowser, QMessageBox, QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtCore import QDate, QUrl, QSettings
from PyQt5.QtGui import QDesktopServices

API_KEY = "3aeace82f952472ab2151a44cf0e736b"
SCHOOL_API_URL = "https://open.neis.go.kr/hub/schoolInfo"
MEAL_API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

STYLESHEET = """
    QWidget {
        background-color: #2E3440;
        color: #D8DEE9;
        font-family: 'Malgun Gothic', Arial, sans-serif;
    }
    QLineEdit {
        background-color: #3B4252;
        border: 1px solid #4C566A;
        padding: 8px;
        border-radius: 5px;
        color: #ECEFF4;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 1px solid #88C0D0;
    }
    QPushButton {
        background-color: #5E81AC;
        color: #ECEFF4;
        border: none;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #81A1C1;
    }
    QPushButton#link_button {
        background-color: #4C566A;
    }
    QPushButton#link_button:hover {
        background-color: #5E81AC;
    }
    QTextBrowser {
        background-color: #3B4252;
        border: 1px solid #4C566A;
        border-radius: 5px;
        color: #E5E9F0;
        font-size: 15px;
    }
    QLabel {
        font-size: 16px;
        font-weight: bold;
        padding-bottom: 5px;
    }
    QMessageBox {
        background-color: #3B4252;
    }
"""

class MealApp(QWidget):
    def __init__(self):
        super().__init__()
        self.school_code = None
        self.office_code = None
        self.initUI()

        # Load last used codes on startup
        settings = QSettings("KyuheonHan", "KyuheonMealApp")
        school_name = settings.value("schoolName", "")
        office_code = settings.value("officeCode", "")
        school_code = settings.value("schoolCode", "")

        if school_name:
            self.school_input.setText(school_name)
        if office_code and school_code:
            self.office_code = office_code
            self.school_code = school_code
            self.office_code_display.setText(office_code)
            self.school_code_display.setText(school_code)

    def initUI(self):
        self.setWindowTitle("Kyuheon's 학교 급식 정보 조회 앱")
        self.setObjectName("MealApp")

        vbox = QVBoxLayout()
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.setSpacing(15)

        self.school_label = QLabel('학교 이름을 입력하세요')

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.school_input = QLineEdit()
        self.school_input.setPlaceholderText("예: 가나고등학교")
        self.school_input.textChanged.connect(self.clear_school_codes)
        input_layout.addWidget(self.school_input)
        
        self.link_button = QPushButton('코드 조회')
        self.link_button.setObjectName("link_button")
        self.link_button.setToolTip('입력된 학교 이름으로 코드를 조회합니다.')
        self.link_button.clicked.connect(self.show_school_codes)
        input_layout.addWidget(self.link_button)

        code_layout = QHBoxLayout()
        code_layout.setSpacing(10)

        office_code_label = QLabel("교육청 코드:")
        self.office_code_display = QLineEdit()
        self.office_code_display.setReadOnly(True)
        code_layout.addWidget(office_code_label)
        code_layout.addWidget(self.office_code_display)

        school_code_label = QLabel("학교 코드:")
        self.school_code_display = QLineEdit()
        self.school_code_display.setReadOnly(True)
        code_layout.addWidget(school_code_label)
        code_layout.addWidget(self.school_code_display)
        
        self.search_button = QPushButton('이번 주 급식 조회')
        self.search_button.clicked.connect(self.fetch_meal_data)

        self.result_display = QTextBrowser()

        vbox.addWidget(self.school_label)
        vbox.addLayout(input_layout)
        vbox.addLayout(code_layout)
        vbox.addWidget(self.search_button)
        vbox.addWidget(self.result_display)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 550, 700)
        self.show()

    def clear_school_codes(self):
        self.office_code = None
        self.school_code = None
        self.office_code_display.clear()
        self.school_code_display.clear()

    def show_school_codes(self):
        school_name = self.school_input.text()
        if not school_name:
            self.show_error("학교 이름을 먼저 입력해주세요.")
            return

        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        office_code, school_code, error_msg = self.find_school(school_name)
        QApplication.restoreOverrideCursor()

        if error_msg:
            self.show_error(error_msg)
        else:
            self.office_code = office_code
            self.school_code = school_code
            self.office_code_display.setText(self.office_code)
            self.school_code_display.setText(self.school_code)

            # Save the successfully retrieved codes
            settings = QSettings("KyuheonHan", "KyuheonMealApp")
            settings.setValue("schoolName", school_name)
            settings.setValue("officeCode", self.office_code)
            settings.setValue("schoolCode", self.school_code)

            QMessageBox.information(self, '코드 조회 완료', f"'{school_name}'의 코드를 찾았습니다.")
            
            url = QUrl("https://open.neis.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=OPEN17320190722180924242823&infSeq=1&cateId=C0001")
            QDesktopServices.openUrl(url)

    def find_school(self, school_name):
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': 1,
            'pSize': 10,
            'SCHUL_NM': school_name
        }
        try:
            response = requests.get(SCHOOL_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'schoolInfo' in data:
                schools = data['schoolInfo'][1]['row']
                if not schools:
                    return None, None, f"'{school_name}'에 해당하는 학교를 찾을 수 없습니다."
                
                office_code = schools[0]['ATPT_OFCDC_SC_CODE']
                school_code = schools[0]['SD_SCHUL_CODE']
                return office_code, school_code, None
            else:
                error_code = data.get('RESULT', {}).get('CODE', 'UNKNOWN')
                error_msg = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류가 발생했습니다.')
                return None, None, f"학교 정보 조회 실패: {error_msg} (코드: {error_code})"
        except requests.exceptions.RequestException as e:
            return None, None, f"네트워크 오류가 발생했습니다: {e}"
        except (KeyError, IndexError):
            return None, None, "학교 정보 응답을 처리하는 중 오류가 발생했습니다. API 응답 형식을 확인하세요."
    
    def fetch_meal_data(self):
        school_name = self.school_input.text()
        if not school_name:
            self.show_error("학교 이름을 입력해주세요.")
            return
            
        if not self.office_code or not self.school_code:
            self.show_error("먼저 '코드 조회' 버튼을 눌러 학교 코드를 찾아주세요.")
            return

        self.result_display.clear()
        self.result_display.append(f"<b>'{school_name}'</b>의 급식 정보를 불러옵니다...")
        QApplication.processEvents()

        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)

        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': 1,
            'pSize': 100,
            'ATPT_OFCDC_SC_CODE': self.office_code,
            'SD_SCHUL_CODE': self.school_code,
            'MLSV_FROM_YMD': start_of_week.strftime('%Y%m%d'),
            'MLSV_TO_YMD': end_of_week.strftime('%Y%m%d')
        }

        try:
            response = requests.get(MEAL_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.result_display.clear()

            if 'mealServiceDietInfo' in data:
                meal_data = data['mealServiceDietInfo'][1]['row']
                
                meals_by_date = {}
                for meal in meal_data:
                    date = meal['MLSV_YMD']
                    if date not in meals_by_date:
                        meals_by_date[date] = []
                    meals_by_date[date].append(meal)
                
                if not meals_by_date:
                    self.result_display.append("이번 주 급식 정보가 없습니다.")
                    return
                
                for date in sorted(meals_by_date.keys()):
                    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                    day_of_week = QDate.fromString(date, "yyyyMMdd").toString("ddd")
                    self.result_display.append(f"<b>--- {formatted_date} ({day_of_week}) ---</b>")
                    
                    sorted_meals_for_day = sorted(meals_by_date[date], key=lambda x: x['MMEAL_SC_CODE'])

                    for meal in sorted_meals_for_day:
                        meal_type = meal['MMEAL_SC_NM']
                        menu = meal['DDISH_NM'].replace('<br/>', '\n')
                        
                        self.result_display.append(f"<b>[{meal_type}]</b>")
                        self.result_display.append(menu)
                        self.result_display.append("-" * 20)
            else:
                error_code = data.get('RESULT', {}).get('CODE', 'UNKNOWN')
                if error_code == 'INFO-200':
                    self.result_display.append("이번 주 급식 정보가 없습니다.")
                else:
                    error_msg = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류가 발생했습니다.')
                    self.show_error(f"급식 정보 조회 실패: {error_msg} (코드: {error_code})")
        
        except requests.exceptions.RequestException as e:
            self.show_error(f"네트워크 오류: {e}")
        except (KeyError, IndexError):
            self.result_display.clear()
            self.result_display.append("급식 정보가 없거나 API 응답 형식에 문제가 있습니다.")

    def show_error(self, message):
        QMessageBox.critical(self, '오류', message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    ex = MealApp()
    sys.exit(app.exec_()) 