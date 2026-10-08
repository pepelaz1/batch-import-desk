import unittest, tempfile, os, io, base64
import engine
class Imports(unittest.TestCase):
    def setUp(self): engine.DB=os.path.join(os.getcwd(),'test-'+__import__('uuid').uuid4().hex+'.sqlite3')
    def tearDown(self): os.remove(engine.DB) if os.path.exists(engine.DB) else None
    def test_validation_and_idempotent_retry(self):
        data={'csv':engine.SAMPLE};r=engine.preview(data)
        self.assertEqual((r['valid'],r['invalid']),(3,2));self.assertEqual(engine.state()['products'],[])
        self.assertEqual(engine.action('/api/import',data)['imported'],3)
        self.assertTrue(engine.action('/api/import',data)['replayed']);self.assertEqual(len(engine.state()['products']),3)
    def test_existing_duplicate_and_nonfinite_price(self):
        engine.action('/api/import',{'csv':engine.SAMPLE})
        r=engine.preview({'csv':'Code,Product,Quantity,Price\nSKU-101,Same,1,NaN'})
        self.assertIn('Duplicate SKU',r['rows'][0]['errors']);self.assertEqual(r['valid'],0)
    def test_mapping_and_xlsx(self):
        from openpyxl import Workbook
        wb=Workbook();wb.active.append(['id','title','stock','cost']);wb.active.append(['A','Desk',5,12.5]);buf=io.BytesIO();wb.save(buf)
        r=engine.preview({'format':'xlsx','file':base64.b64encode(buf.getvalue()).decode(),'mapping':dict(zip(['sku','name','quantity','price'],['id','title','stock','cost']))})
        self.assertEqual(r['valid'],1);self.assertEqual(r['rows'][0]['item']['price'],'12.50')
