import pymunk as pm

def create_body(pos, size, type, mass = None, friction = None, collision_type = 0, moment = None, elasticity = 0.2):
    body = pm.Body(body_type=type)
    body.position = pos

    shape = pm.Poly.create_box(body, size)
    shape.collision_type = collision_type
    shape.elasticity = elasticity

    if type == pm.Body.DYNAMIC:
        shape.mass = mass

    if friction != None:
        shape.friction = friction

    if moment:
        body.moment = moment

    return body, shape
