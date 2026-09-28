import unittest
from unittest.mock import patch
from core.hub_article_reader import extract_article, public_address, read_article
class ArticleTests(unittest.TestCase):
 def test_article_text_and_no_navigation(self):
  text='Contenido completo de prueba. '*30
  data=extract_article('<title>Noticia</title><nav><p>No incluir</p></nav><article><h2>Tema</h2><p>'+text+'</p><script>alert(1)</script></article>')
  self.assertEqual(data['title'],'Noticia')
  self.assertNotIn('No incluir',str(data));self.assertNotIn('alert',str(data))
 def test_summary_is_not_a_full_article(self):
  with self.assertRaises(ValueError):extract_article('<p>Resumen corto.</p>')
 def test_paywall(self):
  with self.assertRaises(ValueError):extract_article('<script type="application/ld+json">{"isAccessibleForFree":false,"articleBody":"'+('texto '*100)+'"}</script>')
 def test_private_and_mixed_dns(self):
  for addresses in [['127.0.0.1'],['169.254.169.254'],['8.8.8.8','10.0.0.1'],['::1']]:
   with patch('socket.getaddrinfo',return_value=[(2,1,6,'',(a,443)) for a in addresses]):
    with self.assertRaises(ValueError):public_address('example.com')
 def test_only_post_ids(self):
  with self.assertRaises(ValueError):read_article('https://localhost')
if __name__=='__main__':unittest.main()
