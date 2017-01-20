
import tensorflow as tf
import sugartensor as stf

from tf_operator.decoder_residual_block.seq_dense \
    import seq_dense
from tf_operator.decoder_residual_block.seq_causal_aconv1d \
    import seq_causal_aconv1d


def seq_decoder_residual_block_init(tensor,
                                    size=3, rate=1):
    default_name = f"lyr-seq-decoder-res-block-{size}-{rate}-init"

    with tf.name_scope(None, default_name, [tensor]):
        # input dimension
        in_dim = tensor.get_shape().as_list()[-1]
        batches = tf.shape(tensor)[0]

        # create zero array
        previous_size = (size - 1) * rate
        init = tf.zeros(
            (batches, in_dim // 2),
            dtype=tensor.dtype,
            name="seq-decoder-residual-block-init-zero"
        )

        # repeat zero
        return (init, ) * previous_size


def seq_decoder_residual_block(tensor, previous,
                               size=3, rate=1,
                               name=None, reuse=False):
    default_name = f"lyr-seq-decoder-res-block-{size}-{rate}"

    scope_variables = [tensor] + list(previous)
    with tf.variable_scope(name, default_name, scope_variables, reuse=reuse):
        # input dimension
        in_dim = tensor.get_shape().as_list()[-1]

        # reduce dimension
        pre_aconv = tensor.sg_bypass(act='relu', ln=True,
                                     name="activation")
        pre_aconv = seq_dense(pre_aconv, dim=in_dim // 2,
                              act='relu', ln=True,
                              name="reduce-dim")

        # 1xk conv dilated
        aconv = seq_causal_aconv1d(pre_aconv, previous=previous,
                                   size=size, rate=rate,
                                   act='relu', ln=True,
                                   name="conv-dilated")

        # dimension recover and residual connection
        out = seq_dense(aconv,
                        dim=in_dim,
                        name="recover-dim") + tensor

        # return (
        #  the input for the same layer in next iteration
        #  the input for the next layer in same iteration
        # )
        return ((pre_aconv, ) + previous[:-1], out)