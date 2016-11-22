import numpy as np
import theano
import theano.tensor as T

from neupy import layers
from neupy.utils import asfloat

from base import BaseTestCase


class ParallelLayerTestCase(BaseTestCase):
    def test_parallel_layer(self):
        input_layer = layers.Input((3, 8, 8))
        parallel_layer = layers.Parallel(
            [[
                layers.Convolution((11, 5, 5)),
            ], [
                layers.Convolution((10, 3, 3)),
                layers.Convolution((5, 3, 3)),
            ]],
            layers.Concatenate(),
        )
        output_layer = layers.MaxPooling((2, 2))

        conn = layers.join(input_layer, parallel_layer)
        output_connection = layers.join(conn, output_layer)
        output_connection.initialize()

        x = T.tensor4()
        y = theano.function([x], conn.output(x))

        x_tensor4 = asfloat(np.random.random((10, 3, 8, 8)))
        output = y(x_tensor4)
        self.assertEqual(output.shape, (10, 11 + 5, 4, 4))

        output_function = theano.function([x], output_connection.output(x))
        final_output = output_function(x_tensor4)
        self.assertEqual(final_output.shape, (10, 11 + 5, 2, 2))

    def test_parallel_with_joined_connections(self):
        # Should work without errors
        layers.Parallel(
            [
                layers.Convolution((11, 5, 5)) > layers.Relu(),
                layers.Convolution((10, 3, 3)) > layers.Relu(),
            ],
            layers.Concatenate() > layers.Relu(),
        )

    def test_parallel_layer_exceptions(self):
        with self.assertRaises(ValueError):
            layers.Parallel(layers.Convolution((11, 5, 5)),
                            layers.Concatenate())

        with self.assertRaises(ValueError):
            layers.Parallel([[layers.Convolution((11, 5, 5))]],
                            'not a layer object')

    def test_parallel_layer_with_residual_connections(self):
        connection = layers.Input((3, 8, 8)) > layers.Parallel(
            [[
                layers.Convolution((7, 1, 1)),
                layers.Relu()
            ], [
                # Residual connection
            ]],
            layers.Concatenate(),
        )
        self.assertEqual(connection.output_shape, (10, 8, 8))