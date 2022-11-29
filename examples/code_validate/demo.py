from beet import Context, Function, PluginOptions


class DemoOptions(PluginOptions):
    message: str
    repeat: int


def beet_default(ctx: Context):
    config = ctx.validate("demo", DemoOptions)

    ctx.data["demo:foo"] = Function([f"say {config.message}"] * config.repeat)
