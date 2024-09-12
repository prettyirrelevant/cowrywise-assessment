import grpc
import pytest

from pagekeeper.protos import pagekeeper_pb2


def test_register(stub):
    request = pagekeeper_pb2.RegisterRequest(
        email='emma.wilson@example.com',
        password='P@ssw0rd123!',
        first_name='Emma',
        last_name='Wilson',
        is_admin=False,
    )
    response = stub.Register(request)
    assert response.message == 'registration successful'
    assert response.id.startswith('user_')


def test_register_duplicate_email(stub):
    first_request = pagekeeper_pb2.RegisterRequest(
        email='emma.wilson@example.com',
        password='P@ssw0rd123!',
        first_name='Emma',
        last_name='Wilson',
        is_admin=False,
    )
    stub.Register(first_request)

    second_request = pagekeeper_pb2.RegisterRequest(
        email='emma.wilson@example.com',
        password='P@ssw0rd123!',
        first_name='Emma',
        last_name='Wilson',
        is_admin=False,
    )

    with pytest.raises(grpc.RpcError) as excinfo:
        stub.Register(second_request)
    assert excinfo.value.code() == grpc.StatusCode.ALREADY_EXISTS


def test_authenticate_success(stub):
    email = 'sophia.lee@example.com'
    password = 'SecureP@ss123!'
    register_request = pagekeeper_pb2.RegisterRequest(
        email=email,
        password=password,
        first_name='Sophia',
        last_name='Lee',
        is_admin=False,
    )
    stub.Register(register_request)

    auth_request = pagekeeper_pb2.AuthenticateRequest(email=email, password=password)
    response = stub.Authenticate(auth_request)
    assert response.message == 'access token returned successfully'
    assert response.access_token
    assert response.user.email == email


def test_authenticate_failure(stub):
    auth_request = pagekeeper_pb2.AuthenticateRequest(email='nonexistent@example.com', password='WrongP@ssword!')
    with pytest.raises(grpc.RpcError) as excinfo:
        stub.Authenticate(auth_request)
    assert excinfo.value.code() == grpc.StatusCode.UNAUTHENTICATED


def test_verify_success(stub):
    email = 'ethan.taylor@example.com'
    password = 'V3rifyP@ss!'
    register_request = pagekeeper_pb2.RegisterRequest(
        email=email,
        password=password,
        first_name='Ethan',
        last_name='Taylor',
        is_admin=False,
    )
    stub.Register(register_request)

    auth_response = stub.Authenticate(pagekeeper_pb2.AuthenticateRequest(email=email, password=password))
    verify_response = stub.Verify(pagekeeper_pb2.VerifyRequest(access_token=auth_response.access_token))
    assert verify_response.message == 'successful verification'
    assert verify_response.user.email == email


def test_verify_failure(stub):
    verify_request = pagekeeper_pb2.VerifyRequest(access_token='invalid_token')
    with pytest.raises(grpc.RpcError) as excinfo:
        stub.Verify(verify_request)
    assert excinfo.value.code() == grpc.StatusCode.UNAUTHENTICATED


def test_fetch_users(stub):
    users = [
        ('ava.johnson@example.com', 'Ava', 'Johnson'),
        ('noah.smith@example.com', 'Noah', 'Smith'),
        ('isabella.williams@example.com', 'Isabella', 'Williams'),
    ]
    user_ids = []
    for email, first_name, last_name in users:
        response = stub.Register(
            pagekeeper_pb2.RegisterRequest(
                email=email,
                password='UserP@ss123!',
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
            )
        )
        user_ids.append(response.id)

    response = stub.FetchUsers(pagekeeper_pb2.FetchUsersRequest(ids=user_ids))
    assert response.message == 'users fetched successfully'
    assert len(response.users) == 3
    assert response.total_users == 3
    assert response.current_page == 1


def test_fetch_users_with_ids(stub):
    user_ids = []
    users = [
        ('liam.davis@example.com', 'Liam', 'Davis'),
        ('mia.anderson@example.com', 'Mia', 'Anderson'),
        ('lucas.martinez@example.com', 'Lucas', 'Martinez'),
        ('charlotte.garcia@example.com', 'Charlotte', 'Garcia'),
        ('mason.lopez@example.com', 'Mason', 'Lopez'),
    ]
    for email, first_name, last_name in users:
        response = stub.Register(
            pagekeeper_pb2.RegisterRequest(
                email=email,
                password='FetchP@ss123!',
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
            )
        )
        user_ids.append(response.id)

    response = stub.FetchUsers(pagekeeper_pb2.FetchUsersRequest(ids=user_ids))
    assert response.message == 'users fetched successfully'
    assert len(response.users) == 5
    assert response.total_users == 5
    assert response.current_page == 1


def test_fetch_users_without_ids(stub):
    users = [
        ('Harper', 'Wilson'),
        ('Evelyn', 'Moore'),
        ('Elijah', 'Taylor'),
        ('Abigail', 'Anderson'),
        ('James', 'Thomas'),
        ('Emily', 'Jackson'),
        ('Benjamin', 'White'),
        ('Elizabeth', 'Harris'),
        ('Lucas', 'Martin'),
        ('Avery', 'Thompson'),
    ] * 6

    for i, (first, last) in enumerate(users, start=1):
        email = f'{first.lower()}.{last.lower()}{i:02d}@example.com'
        stub.Register(
            pagekeeper_pb2.RegisterRequest(
                email=email,
                password='P@gination123!',
                first_name=first,
                last_name=last,
                is_admin=False,
            )
        )

    # Fetch first page
    response_page1 = stub.FetchUsers(pagekeeper_pb2.FetchUsersRequest(page=1, page_size=30))
    assert response_page1.message == 'users fetched successfully'
    assert len(response_page1.users) == 30
    assert response_page1.total_users == 60
    assert response_page1.current_page == 1

    # Fetch second page
    response_page2 = stub.FetchUsers(pagekeeper_pb2.FetchUsersRequest(page=2, page_size=30))
    assert response_page2.message == 'users fetched successfully'
    assert len(response_page2.users) == 30
    assert response_page2.total_users == 60
    assert response_page2.current_page == 2

    # Verify that all users are unique across pages
    unique_emails = {user.email for user in response_page1.users}.union(user.email for user in response_page2.users)
    assert len(unique_emails) == 60

    # Try to fetch a non-existent page
    response_non_existent = stub.FetchUsers(pagekeeper_pb2.FetchUsersRequest(page=3, page_size=30))
    assert response_non_existent.message == 'users fetched successfully'
    assert len(response_non_existent.users) == 0
    assert response_non_existent.total_users == 60
    assert response_non_existent.current_page == 3
