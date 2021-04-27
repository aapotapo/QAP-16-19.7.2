from api import PetFriends
from settings import valid_email, valid_password
import os

pf = PetFriends()


def test_get_api_key_for_valid_user(email=valid_email, password=valid_password):
    """ Проверяем что запрос api ключа возвращает статус 200 и в тезультате содержится слово key"""

    # Отправляем запрос и сохраняем полученный ответ с кодом статуса в status, а текст ответа в result
    status, result = pf.get_api_key(email, password)

    # Сверяем полученные данные с нашими ожиданиями
    assert status == 200
    assert 'key' in result


def test_get_api_key_for_invalid_user(email=valid_email):
    """ Проверяем что запрос api ключа возвращает статус 403"""

    # Отправляем запрос и сохраняем полученный ответ с кодом статуса в status, а текст ответа в result
    status, result = pf.get_api_key(email, "")
    assert status == 403
    assert "This user wasn't found in database" in result


def test_get_all_pets_with_valid_key(filter=''):
    """ Проверяем что запрос всех питомцев возвращает не пустой список.
    Для этого сначала получаем api ключ и сохраняем в переменную auth_key. Далее используя этого ключ
    запрашиваем список всех питомцев и проверяем что список не пустой.
    Доступное значение параметра filter - 'my_pets' либо '' """

    _, auth_key = pf.get_api_key(valid_email, valid_password)
    status, result = pf.get_list_of_pets(auth_key, filter)
    print(result)
    assert status == 200
    assert len(result['pets']) > 0


def test_get_all_pets_with_invalid_filter_params():
    """ Проверяем что запрос всех питомцев с указанием неверного значения
    в параметре filter возвращает ошибку 400 Bad request"""

    _, auth_key = pf.get_api_key(valid_email, valid_password)
    status, result = pf.get_list_of_pets(auth_key, "cats")

    assert status == 400


def test_add_new_pet_with_valid_data(name='Барбоскин', animal_type='двортерьер',
                                     age='4', pet_photo='tests/images/cat1.jpeg'):
    """Проверяем что можно добавить питомца с корректными данными"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Добавляем питомца
    status, result = pf.add_new_pet(auth_key, name, animal_type, age, pet_photo)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 200
    assert result['name'] == name

    # Удаляем созданную запись
    pet_id = result['id']
    pf.delete_pet(auth_key, pet_id)


def test_add_new_pet_with_invalid_data(name='Кощей', animal_type='колдун',
                                       age='0', pet_photo='tests/files/test.txt'):
    """Проверяем что при попытке добавить питомца с некорректным файлом изображения
     сервер возвращает ошибку 400 Bad request"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Добавляем питомца
    status, result = pf.add_new_pet(auth_key, name, animal_type, age, pet_photo)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 400


def test_add_new_pet_with_very_large_name(pet_photo='tests/images/cat1.jpeg'):
    """Проверяем что при попытке добавить питомца с очень длинным именем
     сервер возвращает ошибку 400 Bad request"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    name = 'кисонька'
    # Добавляем питомца
    status, result = pf.add_new_pet(auth_key, name * 1000, name, '0', pet_photo)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 400

def test_successful_delete_self_pet():
    """Проверяем возможность удаления питомца"""

    # Получаем ключ auth_key и запрашиваем список своих питомцев
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Проверяем - если список своих питомцев пустой, то добавляем нового и опять запрашиваем список своих питомцев
    if len(my_pets['pets']) == 0:
        pf.add_new_pet(auth_key, "Суперкот", "кот", "3", "tests/images/cat1.jpeg")
        _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Берём id первого питомца из списка и отправляем запрос на удаление
    pet_id = my_pets['pets'][0]['id']
    status, _ = pf.delete_pet(auth_key, pet_id)

    # Ещё раз запрашиваем список своих питомцев
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Проверяем что статус ответа равен 200 и в списке питомцев нет id удалённого питомца
    assert status == 200
    assert pet_id not in my_pets.values()


def test_delete_not_owned_pet():
    """Проверяем что попытка удаления чужого питомца возвращает ошибку"""

    # Получаем ключ auth_key и запрашиваем список своих питомцев
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, pets = pf.get_list_of_pets(auth_key, "")
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")
    not_owned = [x for x in pets['pets'] if x not in my_pets['pets']]

    # Берём id первого питомца из списка и отправляем запрос на удаление
    pet_id = not_owned[0]['id']
    status, _ = pf.delete_pet(auth_key, pet_id)

    # Ещё раз запрашиваем список всех питомцев
    _, pets = pf.get_list_of_pets(auth_key, "")

    # Проверяем что статус ответа равен 403 и питомец не удален
    assert status == 403
    assert pet_id in pets.values()


def test_successful_update_self_pet_info(name='Мурзик', animal_type='Котэ', age=5):
    """Проверяем возможность обновления информации о питомце"""

    # Получаем ключ auth_key и список своих питомцев
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Проверяем - если список своих питомцев пустой, то добавляем нового и опять запрашиваем список своих питомцев
    if len(my_pets['pets']) == 0:
        pf.add_new_pet(auth_key, "Суперкот", "кот", "3", "tests/images/cat1.jpeg")
        _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Если список не пустой, то пробуем обновить его имя, тип и возраст
    if len(my_pets['pets']) > 0:
        status, result = pf.update_pet_info(auth_key, my_pets['pets'][0]['id'], name, animal_type, age)

        # Проверяем что статус ответа = 200 и имя питомца соответствует заданному
        assert status == 200
        assert result['name'] == name

        # Удаляем созданную запись
        pet_id = my_pets['pets'][0]['id']
        pf.delete_pet(auth_key, pet_id)
    else:
        # если спиок питомцев пустой, то выкидываем исключение с текстом об отсутствии своих питомцев
        raise Exception("There is no my pets")


def test_update_not_owned_pet_info(name='Мурзик', animal_type='Котэ', age=5):
    """Проверяем что попытка обновления информации о чужом питомце возвращает ошибку 403"""

    # Получаем ключ auth_key и список своих питомцев
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, pets = pf.get_list_of_pets(auth_key, "")
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")
    not_owned = [x for x in pets['pets'] if x not in my_pets['pets']]

    # Если список не пустой, то пробуем обновить его имя, тип и возраст
    if len(not_owned) > 0:
        status, result = pf.update_pet_info(auth_key, not_owned[0]['id'], name, animal_type, age)

        # Проверяем что статус ответа = 403
        assert status == 403

    else:
        # если спиок питомцев пустой, то выкидываем исключение с текстом об отсутствии питомцев
        raise Exception("There is no pets")


def test_add_new_pet_no_photo_with_valid_data(name='Барбоскин', animal_type='двортерьер',
                                              age='4'):
    """Проверяем что можно добавить питомца без фото с корректными данными"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Добавляем питомца без фото
    status, result = pf.add_new_pet_without_photo(auth_key, name, animal_type, age)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 200
    assert result['name'] == name
    assert result['pet_photo'] == ""

    # Удаляем созданную запись
    pet_id = result['id']
    pf.delete_pet(auth_key, pet_id)


def test_add_new_pet_no_photo_with_invalid_age(name='Кощей', animal_type='колдун',
                                              age='бессмертный'):
    """Проверяем что попытка добавить питомца с неверным возрастом"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Добавляем питомца без фото
    status, result = pf.add_new_pet_without_photo(auth_key, name, animal_type, age)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 400


def test_set_photo_with_valid_data(name='Барбоскин', animal_type='двортерьер',
                                   age='4'):
    """Проверяем что можно добавить питомца без фото с корректными данными"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Добавляем питомца без фото
    _, result = pf.add_new_pet_without_photo(auth_key, name, animal_type, age)

    status, result = pf.set_photo(auth_key, result['id'], "tests/images/cat1.jpeg")

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 200
    assert result['name'] == name
    assert result['pet_photo'] != ""

    # Удаляем созданную запись
    pet_id = result['id']
    pf.delete_pet(auth_key, pet_id)


def test_set_photo_to_not_owned_pet():
    """Проверяем что при попытке изменить фото чужого питомца сервер возвращает ошибку"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, pets = pf.get_list_of_pets(auth_key, "")
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")
    not_owned = [x for x in pets['pets'] if x not in my_pets['pets']]

    status, result = pf.set_photo(auth_key, not_owned[0]['id'], "tests/images/cat1.jpeg")

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 403
