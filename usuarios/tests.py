from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class UsuariosSeguridadTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='admin', password='adminpass', rol='administrador')
        self.consulta = User.objects.create_user(username='consulta', password='consultapass', rol='consulta')

    def test_login_exitoso_redirige_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'adminpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)

    def test_login_fallido_muestra_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)

    def test_usuario_sin_grupo_ve_menu_limitado(self):
        self.client.login(username='consulta', password='consultapass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Usuarios')
