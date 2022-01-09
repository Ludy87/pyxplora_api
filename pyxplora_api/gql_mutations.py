MUTATION = {
    "tokenM": "mutation IssueToken($countryPhoneNumber: String!, $phoneNumber: String!, $password: String!, $userLang: String!, $timeZone: String!) {\n  issueToken(countryPhoneNumber: $countryPhoneNumber, phoneNumber: $phoneNumber, password: $password, userLang: $userLang, timeZone: $timeZone) {\n    __typename\n    id\n    token\n    issueDate\n    expireDate\n    user {\n      __typename\n      ...UserFragment\n    }\n    app {\n      __typename\n      ...AppFragment\n    }\n    valid\n    w360 {\n      __typename\n      token\n      secret\n      qid\n    }\n  }\n}\nfragment UserFragment on User {\n  __typename\n  id\n  userId\n  name\n  nickname\n  gender\n  birth\n  birthStr\n  weight\n  height\n  countryCode\n  emailAddress\n  countryPhoneCode\n  phoneNumber\n  mobilePhoneNumber\n  emailConfirm\n  status\n  file {\n    __typename\n    ...FileFragment\n  }\n  extra\n  xcoin\n  currentStep\n  totalStep\n  create\n  update\n  children {\n    __typename\n    id\n    guardian {\n      __typename\n      ...SimpleUserFragment\n    }\n    ward {\n      __typename\n      ...SimpleUserFragment\n    }\n  }\n}\nfragment FileFragment on File {\n  __typename\n  id\n  name\n}\nfragment SimpleUserFragment on User {\n  __typename\n  id\n  userId\n  name\n  nickname\n  gender\n  countryCode\n  countryPhoneCode\n  phoneNumber\n  mobilePhoneNumber\n  file {\n    __typename\n    ...FileFragment\n  }\n  xcoin\n  currentStep\n  totalStep\n  contacts {\n    __typename\n    ...ContactsFragment\n  }\n}\nfragment ContactsFragment on Contact {\n  __typename\n  id\n  me {\n    __typename\n    ...ContactorFragment\n  }\n  contacter {\n    __typename\n    ...ContactorFragment\n  }\n  phoneNumber\n  extra\n  listOrder\n  file {\n    __typename\n    ...FileFragment\n  }\n  create\n  update\n}\nfragment ContactorFragment on User {\n  __typename\n  id\n  userId\n  name\n  nickname\n  countryCode\n  countryPhoneCode\n  mobilePhoneNumber\n  phoneNumber\n}\nfragment AppFragment on App {\n  __typename\n  id\n  name\n  packageName\n  apiKey\n  apiSecret\n  terminalType\n  description\n  status\n  versions {\n    __typename\n    ...VersionFragment\n  }\n  create\n  update\n}\nfragment VersionFragment on AppVersion {\n  __typename\n  id\n  version\n  requireUpdate\n  downloadUrl\n  description\n  create\n  update\n}",
    "sendTextM": "mutation SendChatText($uid : String!, $text : String!) {\n  sendChatText(uid: $uid, text: $text)\n}",
    "modifyAlertM": "mutation modifyAlert($uid: String!, $remind: YesOrNo!) {\n  modifyAlert(uid: $uid, remind: $remind)\n}",
    "shutdownM": "mutation ShutDown($uid: String!) {\n  shutDown(uid: $uid)\n}",
    "rebootM": "mutation reboot($uid : String!) {\n  reboot(uid: $uid)\n}",
    "addStepM": "mutation AddStep($stepCount: Int) {\n  addStep(stepCount: $stepCount)\n}",
    "setEnableSlientTimeM": "mutation SetEnableSlientTime($silentId : String!, $status: NormalStatus!) {\n  setEnableSilentTime(silentId: $silentId, status: $status)\n}",
    "setReadChatMsg": "mutation setReadChatMsg($uid: String!, $msgId : String, $id : String) {\n  setReadChatMsg(uid: $uid, msgId: $msgId, id: $id)\n}",
    "ModifyAlarmM": "mutation ModifyAlarm($alarmId: String!, $name: String, $occurMin: Int, $start: Int, $end: Int, $weekRepeat: String, $description: String, $status: NormalStatus, $extra: JSON, $timeZone: String) {\n  modifyAlarm(alarmId: $alarmId, name: $name, occurMin: $occurMin, status: $status, end: $end, weekRepeat:     $weekRepeat, description: $description, start: $start, extra: $extra, timeZone: $timeZone)\n}",
}