import json
import app
import unittest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import app, db, addProductos, Producto, deleteProducto, ProductoCarrito, Carrito, Cliente

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_productos(self):
        producto_data = {
            'id_producto': 1,
            'nombre': 'Producto de prueba',
            'valor_venta': 10.99,
            'stock': 100
        }

        response = self.app.post('/productos', json=producto_data)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id_producto'], producto_data['id_producto'])
        self.assertEqual(data['nombre'], producto_data['nombre'])
        self.assertEqual(data['valor_venta'], producto_data['valor_venta'])
        self.assertEqual(data['stock'], producto_data['stock'])

        producto = Producto.query.filter_by(id_producto=producto_data['id_producto']).first()
        self.assertIsNotNone(producto)
        self.assertEqual(producto.nombre, producto_data['nombre'])
        self.assertEqual(producto.valor_venta, producto_data['valor_venta'])
        self.assertEqual(producto.stock, producto_data['stock'])

    def test_add_existing_product(self):
        existing_product = Producto(id_producto=1, nombre='Producto existente', valor_venta=10.0, stock=5)
        db.session.add(existing_product)
        db.session.commit()

        new_product = {
            'id_producto': 1,
            'nombre': 'Nuevo producto',
            'valor_venta': 15.0,
            'stock': 3
        }

        response = self.app.post('/productos', json=new_product)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'El producto con el ID proporcionado ya existe')

    def test_delete_product(self):
        producto = Producto(id_producto=1, nombre='Producto a eliminar', valor_venta=10.0, stock=5)
        db.session.add(producto)
        db.session.commit()

        response = self.app.delete('/productos/1')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id_producto'], producto.id_producto)
        self.assertEqual(data['nombre'], producto.nombre)
        self.assertEqual(data['valor_venta'], producto.valor_venta)
        self.assertEqual(data['stock'], producto.stock)

        producto_eliminado = Producto.query.filter_by(id_producto=producto.id_producto).first()
        self.assertIsNone(producto_eliminado)

    def test_delete_nonexistent_product(self):
        response = self.app.delete('/productos/999')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['mensaje'], 'Producto no encontrado')

    def test_add_cliente(self):
        cliente_data = {
            'rut': '12345678-9',
            'tarjeta': '1234567890123456'
        }

        response = self.app.post('/clientes', json=cliente_data)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['rut'], cliente_data['rut'])
        self.assertEqual(str(data['tarjeta']), cliente_data['tarjeta'])

        cliente = Cliente.query.filter_by(rut=cliente_data['rut']).first()
        self.assertIsNotNone(cliente)
        self.assertEqual(cliente.rut, cliente_data['rut'])
        self.assertEqual(str(cliente.tarjeta), cliente_data['tarjeta'])

    def test_addProductoCarrito_success(self):
        with app.test_request_context():
            carrito = Carrito(id_carrito=1, total=0)
            db.session.add(carrito)
            db.session.commit()

            producto_data = {
                'id_producto': 1,
                'nombre': 'Producto de prueba',
                'valor_venta': 10.99,
                'stock': 100
            }
            producto = Producto(**producto_data)
            db.session.add(producto)
            db.session.commit()

            payload = {
                'id_producto': 1,
                'id_carrito': 1,
                'cantidad': 2
            }
            response = self.app.post('/productocarrito', json=payload)
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['id_producto'], payload['id_producto'])
            self.assertEqual(data['id_carrito'], payload['id_carrito'])
            self.assertEqual(data['cantidad'], payload['cantidad'])

            producto_carrito = ProductoCarrito.query.filter_by(id_producto=payload['id_producto'], id_carrito=payload['id_carrito']).first()
            self.assertIsNotNone(producto_carrito)
            self.assertEqual(producto_carrito.cantidad, payload['cantidad'])

            carrito = Carrito.query.get(1)
            self.assertEqual(carrito.total, producto_data['valor_venta'] * payload['cantidad'])

    def test_addProductoCarrito_missing_fields(self):
        with app.test_request_context():
            response = self.app.post('/productocarrito', json={})
            data = response.get_json()

            self.assertEqual(response.status_code, 400)
            self.assertEqual(data['mensaje'], 'Campos requeridos no proporcionados')

    def test_delete_producto_carrito(self):
        with app.test_request_context():
            carrito = Carrito(id_carrito=1, total=0)
            db.session.add(carrito)
            db.session.commit()

            producto_data = {
                'id_producto': 1,
                'nombre': 'Producto de prueba',
                'valor_venta': 10.99,
                'stock': 100
            }
            producto = Producto(**producto_data)
            db.session.add(producto)
            db.session.commit()

            producto_carrito = ProductoCarrito(id_producto=1, id_carrito=1, cantidad=2)
            db.session.add(producto_carrito)
            db.session.commit()

            response = self.app.delete('/productocarrito/1/1')
            data = json.loads(response.data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['mensaje'], 'Producto eliminado del carrito')

            producto_carrito = ProductoCarrito.query.filter_by(id_producto=1, id_carrito=1).first()
            self.assertIsNone(producto_carrito)

            carrito = Carrito.query.get(1)
            self.assertEqual(carrito.total, 0)

    def test_delete_producto_carrito_producto_no_encontrado(self):
        response = self.app.delete('/productocarrito/2/1')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['mensaje'], 'Producto no encontrado en el carrito')

    def test_delete_producto_carrito_carrito_no_encontrado(self):
        response = self.app.delete('/productocarrito/1/2')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['mensaje'], 'Producto no encontrado en el carrito')


if __name__ == '__main__':
    unittest.main()
