# Tabelog Inbound (com.kakaku.tabelog.tourists 2.24.1) API notes

Source: static analysis of the decompiled smali. Nothing here was tested against the live service.

## Client setup

| Item | Value |
|---|---|
| HTTP stack | Retrofit + OkHttp, kotlinx JSON (`application/json`) |
| Base URL | `"https://api." + "tabelog.com"` (assembled in `y2/f.smali`, probably `https://api.tabelog.com`) |
| Proxy config | `Ln3/b` hardcoded to host `52.69.87.243`, port 443 (0x1bb), empty user/pass, enabled flag false |
| User-Agent | `TabelogInbound Android/ver2.24.1` |
| `X-Tabelog-Appli-Version` | `TabelogInbound Android/ver2.24.1` |
| `X-Tabelog-Access-Token` | added by `l9/e` (auth repository) when logged in |
| `X-Tabelog-Secret-Token` | added by `l9/i`; token obtained from `secret_token_generate/create` |
| Error interceptor | `l9/c` handles forced update and forced logout responses |
| Local prefs keys | `secret_token`, `user_credentials`, `uuid`, `proxy_*`, `last_language` (`k9/a`) |
| Third party | Google Routes API `POST https://routes.googleapis.com/directions/v2:computeRoutes` (headers `X-Goog-Api-Key`, `X-Goog-FieldMask`) |

All endpoints live under `/tabelog_inbound_appli/`. Nearly every call takes `lang`. GET params are query strings, POST params are form fields (`@Field`) unless noted JSON.

## Auth flow (inferred)

1. `POST onetime_password/send` JSON `{email, lang}`
2. `POST account/authenticate` JSON `{email, code, lang}` returns `AccountAuthenticateResult`
3. `POST account/token` JSON `{token, lang}` exchanges a token (`AccountTokenExchangeResult`)
4. `POST secret_token_generate/create` form `{lang, code}` yields the secret token
5. Subsequent calls send `X-Tabelog-Access-Token` and `X-Tabelog-Secret-Token`
6. `POST account/register` JSON `{lang, ...}` creates the account

## Endpoints

### Account
- `POST account/authenticate` (JSON body)
- `POST account/register` (JSON body)
- `POST account/token` (JSON body)
- `POST account/update` (JSON body)
- `POST account/logout` form `lang`
- `POST account/profile_update` form `nickname, lang`
- `GET account/latest` `lang`
- `GET account/deletable` `lang`
- `DELETE account/delete` `lang`
- `POST onetime_password/send` (JSON body)
- `POST secret_token_generate/create` form `lang, code`
- `POST push_device_token/register` form `device_token`

### Restaurant
- `GET restaurant_search/index` `page, lang, search_type, area_datatype(_id), genre_datatype(_id), range, latitude, longitude, min/max_latitude, min/max_longitude, fixed_area_search_flg, cost_timezone_type, low_cost_type, high_cost_type, open_on_sunday_flg, business_hour_type, reservation_datetime, reservation_member, reservation_search_mode, situation_type, smoking_type, separation_smoking_flg, reservation_type, parking_flg, card_type_list[], emoney_type_list[], qrcode_payment_type_list[], private_room_type_list[], complete_private_room, charter_type_list[], space_facility_type_list[], food_type_list[], drink_type_list[], course_type_list[], drink_course_type_list[], location_type_list[], kids_type_list[], service_type_list[], sort_mode, current_latitude, current_longitude, reservation_time_range, last_minute_reservation_flg, tabelog_hyakumeiten_all_flg, tabelog_hyakumeiten_category_id_list[], tabelog_award_type_list[], search_tag_category_ids[], search_tag_ids[], domestic_popular_flg, inbound_popular_flg`
- `GET suggest_search/index` `keyword, lang, current_latitude, current_longitude, area_datatype(_id), genre_datatype(_id), search_tag_category_ids[], search_tag_ids[]`
- `GET restaurant_detail/show` `restaurant_id, lang, test_access_key`
- `GET restaurant_detail_menu_list/index` `restaurant_id, lang`
- `GET restaurant_detail_photo_list/index` `restaurant_id, page, photo_type, lang`
- `GET restaurant_detail_review_list/index` `restaurant_id, page, use_type, lang`
- `GET restaurant_detail_prosperity_banner_list/index` `restaurant_id, lang`
- `GET restaurant_detail_vacancy_status_on_latest_days/index` `restaurant_id, lang`
- `GET restaurant_vacancy_status_on_latest_days/index` `restaurant_id_list[], lang`
- `GET restaurant_latest/index` `restaurant_id_list[], lang`
- `GET restaurant_reservable_time_information_list/index` `restaurant_id_list[], reservation_datetime, reservation_member, lang`
- `GET total_review/show` `bookmark_id, review_id, lang`
- `GET total_review_photo_list/index` `bookmark_id, page, lang`
- `GET total_review_review_list/index` `bookmark_id, page, lang`
- `GET popular_items/index` `lang, selected_prefecture_ids[]`
- `GET popular_item_nearby/index` `lang, latitude, longitude`
- `GET ai_recommend/index` `lang`
- `GET ai_recommend/show` `lang, date, restaurant_id`
- `GET check_japan_coordinate/index` `latitude, longitude`

### Area master data
- `GET area_area1/index` `lang, prefecture_id`
- `GET area_area2/index` `lang, area1_id`
- `GET area_municipal/index` `lang, prefecture_id`
- `GET area_station/index` `area2_id, lang`

### Reservations
- `GET reservation/list` `lang, page, per_page, sort, booked_flag`
- `GET reservation/show` `yoyaku_code, lang`
- `GET reservation_search_reservable_date/index` `restaurant_id, plan_id, seat_only_flg, lang`
- `GET reservation_search_reservable_member/index` `restaurant_id, plan_id, seat_only_flg, reservation_date, lang`
- `GET reservation_search_reservable_time/index` `restaurant_id, plan_id, reservation_number_of_people, seat_only_flg, reservation_date, reservation_datetime, lang`
- `GET reservation_search_reservable_vacancy/index` `restaurant_id, plan_id, seat_only_flg, lang`

Booking itself opens web views: `appli/booking/form_booking/show`, `appli/booking/edit_form/new?code=`, `appli/booking/booking_cancel/new?code=`.

### Saved lists (hozon)
- `POST hozon_list/create` `title, description, visibility, lang`
- `POST hozon_list/update` `hozon_list_id, title, description, visibility, lang`
- `POST hozon_list/destroy` `hozon_list_id, lang`
- `GET hozon_list/show` `share_token, lang`
- `GET hozon_list_restaurant/index` `hozon_list_id, page, per_page, lang`
- `POST hozon_list_restaurant/update` `restaurant_id, hozon_list_id_list[], is_favorite, is_visited, lang`
- `POST hozon_list_subscription/create` `share_token, lang`
- `POST hozon_list_subscription/destroy` `hozon_list_id, lang`
- `GET hozon_restaurant/index` `page, per_page, prefecture_id, latitude, longitude, lang`
- `POST hozon_restaurant/login_sync` `restaurant_id_list[], lang`
- `POST hozon_sharing/update` `list_type, visibility, lang`

### Visited
- `GET visited_restaurant/index` `page, per_page, prefecture_id, latitude, longitude, lang`
- `POST visited_restaurant/create` `restaurant_id, lang`
- `POST visited_restaurant/destroy` `restaurant_id, lang`

### Notifications and info
- `GET notification/count` `lang`
- `GET notification/list` `lang, page, per_page`
- `POST notification/read` `lang, notification_id`
- `GET information_latest/show`, `information_master_data/show`, `information_message/index` (each `lang`)

## Response models

Package `com.kakaku.tabelog.tourists.domain.response.result` (for example `RestaurantDetailShowResult`, `RestaurantKeywordSearchResult`). Request bodies are in `com.kakaku.tabelog.tourists.infra.network.request`.

## Caveats

- Verb mapping uses Retrofit's alphabetical R8 naming (`Cb.b`=DELETE, `f`=GET, `o`=POST, `t`=Query, `a`=Body); consistent with the observed endpoints.
- Request body field lists for authenticate/token/otp come from the serializer descriptors. `account/register` and `account/update` bodies have only `lang` visible, other fields may be in parent classes.
- Token lifetimes, signing, and server-side rate limits cannot be determined statically.
- Using the service outside the official app may violate Tabelog's terms of service.
