Depth To Water
------------------

.. code-block:: python

   ground surface ------------------| |--------------------------
                                    | |   |       |            |
                                    | |   | d_0   |            |
                                    | |   |       | d_1        |
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

.. math:: d(t) = L` - h
   :label: corrected_drift

where `L\``

.. math:: L` = L_{1} - (L_{1}-L_{0})/(t_{1}-t_{0})*(t-t_{0})
  :label: drift_l

To calculate `depth_to_water` at a given time `t` use :eq:`corrected_no_drift`

To calculate `depth_to_water` at a given time `t` and corrected for drift use :eq:`corrected_drift`

