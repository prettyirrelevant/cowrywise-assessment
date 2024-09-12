from datetime import timedelta


def test_config(config):
    assert config.DATABASE_NAME.startswith('db_')
    assert config.SECRET_KEY == 'test_secret_key'
    assert config.MONGODB_URL == 'mongodb://localhost:27017'
    assert timedelta(hours=24) == config.ACCESS_TOKEN_EXPIRATION
