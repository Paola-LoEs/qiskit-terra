# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Pass for converting a circuit targeting U3,CX basis to Rx,Ry,Rxx."""

from qiskit.transpiler.basepasses import TransformationPass
from qiskit.exceptions import QiskitError

from qiskit.converters import circuit_to_dag
from qiskit.extensions.standard import U3Gate, CnotGate

from qiskit.transpiler.passes import Unroller
from qiskit.quantum_info.synthesis.one_qubit_decompose import OneQubitEulerDecomposer
from qiskit.quantum_info.synthesis.ion_decompose import cnot_rxx_decompose


class MSBasisDecomposer(TransformationPass):
    """
    Convert a circuit in U3,CX to Rx,Ry,Rxx without unrolling or simplification.
    """

    supported_input_gates = (U3Gate, CnotGate)
    supported_basis_names = ('rx', 'ry', 'rxx', 'ms')

    def __init__(self, basis):
        """
        Args:
            basis (list[str]): Target basis names, e.g. `['rx', 'ry', 'rxx', 'ms']` .

        Raises:
            QiskitError: if target basis is not [ 'rx', 'ry', 'rxx', 'ms' ]

        """
        super().__init__()

        self.basis = basis
        self.requires = [Unroller(list(set(basis).union(['u3', 'cx'])))]

    def run(self, dag):
        """Replace U3,CX nodes in input dag with equivalent Rx,Ry,Rxx gates.

        Args:
            dag(DAGCircuit): input dag

        Raises:
            QiskitError: if input dag includes gates outside U3,CX.

        Returns:
            DAGCircuit: output dag
        """

        one_q_decomposer = OneQubitEulerDecomposer(basis='XYX')
        cnot_decomposition = cnot_rxx_decompose()

        for node in dag.op_nodes():
            basic_insts = ['measure', 'reset', 'barrier', 'snapshot']
            if node.name in basic_insts:
                # TODO: this is legacy behavior. basic_insts should be removed and these
                #  instructions should be part of the device-reported basis. Currently, no
                #  backend reports "measure", for example.
                continue
            if node.name in self.basis:  # If already a base, ignore.
                continue

            if not isinstance(node.op, self.supported_input_gates):
                raise QiskitError("Cannot convert the circuit to the given basis, %s. "
                                  "No rule to expand instruction %s." %
                                  (str(self.basis), node.op.name))

            if isinstance(node.op, U3Gate):
                replacement_circuit = one_q_decomposer(node.op)
            elif isinstance(node.op, CnotGate):
                # N.B. We can't circuit_to_dag once outside the loop because
                # substitute_node_with_dag will modify the input DAG if the
                # node to be replaced is conditional.

                replacement_circuit = cnot_decomposition
            else:
                raise QiskitError("Unable to handle instruction (%s, %s)."
                                  % (node.op.name, type(node.op)))

            replacement_dag = circuit_to_dag(replacement_circuit)

            # N.B. wires kwarg can be omitted for both 1Q and 2Q substitutions.
            # For 1Q, one-to-one mapping is always correct. For 2Q,
            # cnot_rxx_decompose follows convention of control as q[0], target
            # as q[1], which matches qarg order in CX node.

            dag.substitute_node_with_dag(node, replacement_dag)

        return dag
