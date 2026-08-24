<p align="center"><a href="https://once-email.com"><img src="../assets/unpack-flow-banner.png" alt="UnpackFlow by Once Email" width="100%"></a></p>

# UnpackFlow — बिना निगरानी नेस्टेड आर्काइव निकालें

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

`-r` में आउटपुट नाम पहले से मौजूद होने पर UnpackFlow स्रोत फ़ोल्डर का नाम जोड़ता है, जैसे `sample-backup-legacy-set-unpacked`; आगे के टकराव में `-2`, `-3` जुड़ते हैं, इसलिए कोई परिणाम बदला या छोड़ा नहीं जाता।

छोटा `unpack-flow-minimal-testcases-v1.zip` ZIP, TAR.GZ, Unicode, नेस्टेड आर्काइव, मल्टीपार्ट `part01.exe` और अनुपस्थित वॉल्यूम की अपेक्षित विफलता जाँचता है; इसमें बड़े ऐप नहीं हैं और SFX कभी चलाया नहीं जाता।

मूल सिस्टम स्वीकृति `/data/unpack-flow-testcases` में सिंथेटिक डेटा का उपयोग करती है; `UNPACK_FLOW_TEST_ROOT` से पथ बदला जा सकता है। बड़े सूट वैकल्पिक हैं और केवल प्रदर्शन या अतिरिक्त प्रारूप संगतता के लिए उपयोग होते हैं।

UnpackFlow सॉफ़्टवेयर वितरण, डेटासेट, बैकअप, मीडिया संसाधन और अन्य बड़े आर्काइव संभालता है। यह पहला वॉल्यूम पहचानता है, नेस्टेड परतें क्रम से निकालता है और पैकेज, चरण, स्तर व समय दिखाता है।

## उपयोग और इंस्टॉल

`unpack-flow list 'Archive*'`, `plan`, `unpack-flow 'Archive*'`, `status`। Linux पर Bash, Windows पर PowerShell 5.1+ व 7-Zip, macOS पर PowerShell 7+ व `7zz` चाहिए। `scripts/build-release.sh` तीनों पैकेज और SHA-256 बनाता है।

`unpack-flow` चलाने या आर्काइव निकालने के लिए Python आवश्यक नहीं है। Python 3 केवल Linux/macOS पर `install_local.py` या `install_local.sh` से Skill की स्वचालित स्थापना और Python ऑडिट के लिए चाहिए। Windows का `install_local.ps1` केवल PowerShell उपयोग करता है; Skill को हाथ से कॉपी करने में भी Python नहीं चाहिए।

## समर्थित एक्सट्रैक्शन कार्य

UnpackFlow डायरेक्टरी और वाइल्डकार्ड से मिले आर्काइव बैच में निकालता है, नेस्टेड आर्काइव को परत-दर-परत खोलता है और multipart RAR का पहला वॉल्यूम पहचानता है। यह अनजान EXE चलाए बिना RAR self-extracting पैकेज भी जाँचता है। यह सॉफ़्टवेयर पैकेज, डेटासेट, बैकअप, मीडिया, लॉग और ISO या WIM इमेज के लिए उपयोगी है।

डिफ़ॉल्ट रूप से यह अधिकतम 10 अंदरूनी परतें खोलता है। खराब या अधूरा अंदरूनी आर्काइव सुरक्षित रखकर दर्ज और छोड़ दिया जाता है, जबकि बाकी काम जारी रहता है; पहली त्रुटि पर रुकने के लिए `-StopOnError` उपयोग करें।

## सीखने के उदाहरण

बैकअप, डेटासेट, लॉग, सॉफ़्टवेयर या मल्टीपार्ट आर्काइव के लिए `list`, `plan`, `start`, `status`, `log` और `wait` उपयोग करें। गेम केवल एक उदाहरण है, उत्पाद की सीमा नहीं।

तीनों प्लेटफ़ॉर्म पर `run` प्रगति के साथ अग्रभूमि में चलता है और `start` पृष्ठभूमि जॉब शुरू करके उसका ID लौटाता है।

लंबे 7-Zip या UnRAR कार्यों के दौरान बीता समय हर सेकंड अपडेट होता है और हर 30 सेकंड में सक्रियता संकेत लॉग होता है।

macOS और Windows पर `start` सभी इंटरैक्टिव टर्मिनल स्ट्रीम अलग करता है; प्रगति केवल लॉग में जाती है और ANSI कोड या बीप नहीं आते।

`-r` या `-Recursive` उपफ़ोल्डरों के सभी आर्काइव और उनकी अंदरूनी परतें खोलता है; समान नाम होने पर परिणाम सुरक्षित रूप से `नाम-unpacked` में जाता है।

`unpack-flow run *` भी समर्थित है। Shell द्वारा `*` फैलाने के बाद स्कैन केवल एकल archive और `part1.exe`, `part1.rar`, `.7z.001`, `.zip.001` जैसे पहले volume रखता है; `.sha256`, असंबंधित फ़ाइलें और बाद के volume हट जाते हैं।

`unpack-flow help` अंग्रेज़ी और सरल चीनी में संयुक्त कमांड सहायता दिखाता है।

## बैकग्राउंड कार्य और लॉग

`unpack-flow start "आर्काइव" -Output "गंतव्य"` बैकग्राउंड एक्सट्रैक्शन शुरू करके जॉब ID देता है। `unpack-flow status [ID]`, `unpack-flow log [ID]` और `unpack-flow wait [ID]` से इसे देखें; ID न देने पर नवीनतम जॉब चुना जाता है। लॉग Windows में `%LOCALAPPDATA%\unpack-flow\state` और macOS/Linux में `~/.local/state/unpack-flow` में रहते हैं।

TAR, TAR.GZ/TGZ और स्वतंत्र GZ समर्थित हैं। 7-Zip के बाद प्रारूप के अनुसार UnRAR, सिस्टम `tar`, GZip या ZIP आज़माया जाता है; हर विफल प्रयास साफ होता है और सभी विकल्प विफल होने पर मूल फ़ाइल व लॉग सुरक्षित रखकर अगला आर्काइव चलता है—अनंत पुनःप्रयास नहीं होता।

Linux x64 पैकेज में आधिकारिक UnRAR 7.23 शामिल है। Windows x64/ARM64 में आधिकारिक पूर्ण 7-Zip 26.02 है और x64 में UnRAR भी है; मूल पैकेज व लाइसेंस सुरक्षित हैं।

## पूरा त्वरित आरंभ

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

बैकग्राउंड में चलाने के लिए:

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` वर्तमान टर्मिनल में रहता है; `start` तुरंत जॉब ID देता है। दोनों मोड मूल आर्काइव सुरक्षित रखते हैं।

## कमांड-लाइन उपकरण इंस्टॉल करें

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

जाँच कमांड अनुपलब्ध निर्भरताएँ बताते हैं, लेकिन सिस्टम सॉफ़्टवेयर अपने आप इंस्टॉल नहीं करते।

## रिकर्सन, लॉग और विफलताएँ

उपफ़ोल्डर और अंदरूनी आर्काइव परतें खोलने के लिए `-r` या `-Recursive` उपयोग करें। डिफ़ॉल्ट सीमा 10 अंदरूनी परतें है।

| प्लेटफ़ॉर्म | डिफ़ॉल्ट स्टेट डायरेक्टरी |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

UnpackFlow सीमित क्रम में 7-Zip, RAR के लिए UnRAR और TAR, GZ या ZIP के उपयुक्त मूल उपकरण आज़माता है। अधूरा आउटपुट साफ किया जाता है। सभी विकल्प विफल होने पर मूल आर्काइव बचता है, त्रुटि लॉग होती है और अगला कार्य चलता है। पहली त्रुटि पर रोकने के लिए ही `-StopOnError` उपयोग करें।

## परीक्षण और Agent Skill इंस्टॉलेशन

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

Windows में Skill को `scripts/install_local.ps1` से इंस्टॉल करें। आर्काइव निकालने के लिए Python आवश्यक नहीं है; यह केवल Linux/macOS के स्वचालित Skill इंस्टॉलर और Python ऑडिट में उपयोग होता है।

## सुरक्षा, परियोजना और सहायता

UnpackFlow स्रोत फ़ाइलें सुरक्षित रखता है, गंतव्यों को ओवरराइट नहीं करता और अज्ञात EXE नहीं चलाता।

- आधिकारिक वेबसाइट: [once-email.com](https://once-email.com)
- निर्माता और डेवलपर: helen.jar
- GitHub परियोजना: [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- सहायता ईमेल: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

किसी भी प्रश्न के लिए [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) पर ईमेल करें या [GitHub Issues में समस्या दर्ज करें](https://github.com/pangxin12345/unpack-flow/issues)।

MIT लाइसेंस, संस्करण 2.1.4।
