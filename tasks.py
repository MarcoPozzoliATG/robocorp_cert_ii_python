import os
import shutil
from robocorp.tasks import task
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.HTTP import HTTP
from RPA.Robocorp.WorkItems import WorkItems
from Browser import Browser, SelectAttribute,ElementState

out_path = os.path.join(os.getcwd(), r"output")
screen_bot_path = os.path.join(out_path, r"screen_bot")
receipts_bot_path = os.path.join(out_path, r"receipts")
pdf = PDF()
archive = Archive()
browser = Browser()
wi = WorkItems()
@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website()


def open_robot_order_website():
    clear_folders()

    browser.new_page()
    browser.go_to("https://robotsparebinindustries.com/#/robot-order")
    
    orders = get_orders()

    
    for order in orders:
        fill_the_form(order)
        screen_png = screenshot_robot(order)
        submit_bot() 
        store_receipt_as_pdf(screen_png,order['Order number'])
        order_new_robot()

    archive_receipts()
    browser.close_page()

def archive_receipts():
    archive_name = "output.zip"
    archive_path = os.path.join(out_path, archive_name)
    archive.archive_folder_with_zip(folder=out_path,archive_name=archive_path,recursive=True)
    
    wi.get_input_work_item()
    wi.create_output_work_item(files=archive_path,save=True)
    wi.release_input_work_item("DONE")

def order_new_robot():
    browser.click("//*[@id='order-another']")
    browser.wait_for_elements_state("//*[contains(@class, 'btn-dark')]",ElementState.visible)

def clear_folders():
    # order
    if os.path.exists("orders.csv"):
        os.remove("orders.csv")
    if os.path.exists(screen_bot_path):
        shutil.rmtree(screen_bot_path, ignore_errors=True)
    os.makedirs(screen_bot_path)

    if os.path.exists(receipts_bot_path):
        shutil.rmtree(receipts_bot_path, ignore_errors=True)
    os.makedirs(receipts_bot_path)

def get_orders():
    HTTP().download("https://robotsparebinindustries.com/orders.csv")
    orders = Tables().read_table_from_csv("orders.csv")
    return orders

def fill_the_form(order):
    close_annoying_modal()
    browser.select_options_by("//*[@id='head']",SelectAttribute["value"],order['Head'])
    xpath = f"//*[@id='id-body-{order['Head']}']"
    browser.check_checkbox(xpath,True)
    browser.fill_text("//input[@placeholder='Enter the part number for the legs']",order['Legs'])
    browser.fill_text("//*[@id='address']",order['Address'])
    
def close_annoying_modal():
    browser.click("//*[contains(@class, 'btn-dark')]")

def screenshot_robot(order):
    browser.click("//*[@id='preview']")
    preview_xpath = f"//*[@id='robot-preview-image']"
    head_xpath = "//div[@id='robot-preview']//img[@alt='Head']"
    body_xpath = "//div[@id='robot-preview']//img[@alt='Body']"
    legs_xpath = "//div[@id='robot-preview']//img[@alt='Legs']"

    browser.wait_for_elements_state(preview_xpath,ElementState.visible)
    browser.wait_for_elements_state(head_xpath,ElementState.visible)
    browser.wait_for_elements_state(body_xpath,ElementState.visible)
    browser.wait_for_elements_state(legs_xpath,ElementState.visible)

    file_name = "preview_bot_" + order['Order number'] + ".png"
    file_screen = os.path.join(screen_bot_path, file_name)
    browser.take_screenshot(filename =file_screen, selector=preview_xpath)
    return file_screen

def submit_bot():
    browser.click("//*[@id='order']")
    done = False
    while not(done):
        try:
            res = browser.wait_for_elements_state("//*[contains(@class, 'alert') and contains(@class, 'alert-danger')]",ElementState.visible,timeout=0.5)
            browser.click("//*[@id='order']")
        except:
            done = True

def store_receipt_as_pdf(screen_png,order_number):
    receipt_HTML = browser.get_property("//*[@id='receipt']",property="outerHTML")    
    file_name = "receipt_bot_" + order_number  + ".pdf"
    file_screen = os.path.join(receipts_bot_path, file_name)
    pdf.html_to_pdf(receipt_HTML,file_screen)
    embed_screenshot_to_receipt(screen_png,file_screen)

def embed_screenshot_to_receipt(screenshot, pdf_file):
    screenshot = screenshot+":align=center"
    pdf.open_pdf(pdf_file)
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True   
    )
    # pdf.close_pdf(pdf_file)
	