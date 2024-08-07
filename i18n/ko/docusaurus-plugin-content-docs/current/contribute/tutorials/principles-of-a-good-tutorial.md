# 좋은 튜토리얼의 원칙

이 원칙을 담은 [talkol](https://github.com/talkol)의 원본 댓글입니다:

- [TON 발자취 #7에 대한 원본 댓글](https://github.com/ton-society/ton-footsteps/issues/7#issuecomment-1187581181)

다음은 신규 기여자를 위한 요점 정리입니다.

## 원칙

1. 전체 흐름은 사용자의 클라이언트에서 실행되어야 합니다. 타사 서비스가 포함되지 않아야 합니다. 사용자가 리포지토리를 간단히 복제하고 즉시 실행할 수 있도록 모든 작업을 수행해야 합니다.

2. README는 매우 상세해야 합니다. 사용자가 아무것도 모른다고 가정하지 마세요. 튜토리얼에 필요한 경우 장치에 FunC 컴파일러나 Lite-client를 설치하는 방법도 설명해야 합니다. 이 문서의 다른 튜토리얼에서 이러한 부분을 복사할 수 있습니다.

3. 저장소에는 사용된 컨트랙트의 전체 소스 코드가 포함되는 것이 좋습니다. 사용자들이 표준 코드를 약간 변경할 수 있도록 하기 위해서입니다. 예를 들어, Jetton 스마트 컨트랙트는 사용자들이 맞춤형 동작을 실험할 수 있도록 합니다.

4. 가능하다면 사용자가 코드를 다운로드하거나 아무것도 구성하지 않고도 프로젝트를 배포하거나 실행할 수 있는 사용자 친화적인 인터페이스를 만들어야 합니다. 이 경우에도 독립형으로 GitHub Pages에서 제공되어 사용자의 장치에서 100% 클라이언트 측에서 실행되도록 해야 합니다. 예: https://minter.ton.org/

5. 각 필드 선택이 무엇을 의미하는지 사용자에게 설명하고 모범 사례를 설명합니다.

6. 보안에 대해 알아야 할 모든 것을 설명합니다. 작성자가 실수를 하지 않고 위험한 스마트 계약/봇/웹사이트를 만들지 않도록 충분히 설명해야 하며, 이는 최고의 보안 관행을 가르치는 것입니다.

7. 이상적으로, 리포지토리에는 독자가 튜토리얼의 맥락에서 이를 구현하는 방법을 잘 보여주는 잘 작성된 테스트가 포함되어야 합니다.

8. 저장소는 자체적으로 이해하기 쉬운 컴파일/배포 스크립트를 포함해야 합니다. 사용자가 단순히 `npm install` 을 하고 이를 사용할 수 있어야 합니다.

9. 때로는 GitHub 리포지토리만으로 충분하고 전체 문서를 작성할 필요가 없습니다. 이 경우 README에 저장소의 모든 코드가 포함되어 있어야 합니다. 코드는 사용자가 쉽게 읽고 이해할 수 있도록 잘 주석이 달려 있어야 합니다.
