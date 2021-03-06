Depth To Water
------------------

.. code-block:: python

   ground surface ------------------| |-------------------------
                                    | |   |       |            |
                                    | |   | d0    |            |
                                    | |   |       | d1         |
                                    | |   |       |            |
   water table t_o    ---------------------       |            |
                      |             | |           |            |  L
                   h0 |             | |           |            |
                      |             | |           |            |
   water table t_1    |        --------------------            |
                      |        |    | |                        |
                      |     h1 |    | |                        |
                      |        |    | |                        |
                      |        |    | |                        |
   sensor             |________|____|*|________________________|



.. math:: d(t) = L - h
   :label: corrected_no_drift

.. math:: d(t) = l(t) - h
   :label: corrected_drift

where :math:`l(t)`

.. math:: l(t) = L_{0} + \frac{(L_{1}-L_{0})}{(t_{1}-t_{0})}*(t-t_{0})
  :label: drift_l

To calculate `depth_to_water` at a given time `t` use :eq:`corrected_no_drift`

To calculate `depth_to_water` at a given time `t` and corrected for drift use :eq:`corrected_drift`

