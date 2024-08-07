# 翻译风格指南

此翻译风格指南包含一些最重要的指南、说明和翻译技巧，帮助我们对网站进行本地化。

本文档是一份一般性指南，并不特定于任何一种语言。

## 理解信息的精髓

当翻译 TON 文档内容时，避免直译。

重要的是翻译要抓住信息的本质。 这可能意味着改写某些短语，或者使用描述性翻译而不是逐字翻译内容。

不同的语言有不同的语法规则、约定和词序。 翻译时，请注意目标语言中句子的结构，避免按字面翻译英文源，因为这会导致句子结构和可读性差。

建议你阅读整个句子并对其进行调整以适应目标语言的惯例，而不是逐字翻译源文本。

## 正式与非正式

我们使用正式的称呼形式，这对所有访客来说始终是礼貌和适当的。

使用正式的称呼可以让我们避免听起来不官方或冒犯，并且无论访客的年龄和性别如何都可以通用。

大多数印欧语和亚非语语言使用特定性别的第二人称人称代词，以区分男性和女性。 在称呼用户或使用所有格代词时，我们可以避免假设访问者的性别，因为正式的称呼形式通常适用且一致，无论他们如何定位自己。

## 简单明了的词汇和意思

我们的目标是让尽可能多的人能够理解网站上的内容。

在大多数情况下，这可以通过使用易于理解的简短单词轻松实现。 如果你的语言中具有相同含义的某个单词有多种可能的翻译，那么最好的选择通常是清楚地反映含义的最短单词。

## 书写系统

所有内容都应使用适合你的语言的正确书写系统进行翻译，并且不应包含使用拉丁字符书写的任何单词。

翻译内容时，应确保翻译内容一致且不包含任何拉丁字符。

**以上规则不适用于通常不应翻译专有名词的语言。**

## 翻译页面元数据

某些页面包含页面上的元数据，例如“title”、“lang”、“description”、“sidebar”等。

在将新页面上传到 Crowdin 时，我们隐藏了翻译人员不应翻译的内容，这意味着 Crowdin 中翻译人员可见的所有元数据都应该被翻译。

翻译源文本为“en”的任何字符串时，请特别注意。 这表示页面可用的语言，应翻译为[你的语言的 ISO 语言代码](https://www.andiamo.co.uk/resources/iso-language-codes/)。 这些字符串应始终使用拉丁字符而不是目标语言原生的书写脚本进行翻译。

如果你不确定要使用哪种语言代码，你可以查看 Crowdin 中的翻译记忆库，或在 Crowdin 在线编辑器的页面 URL 中找到你的语言的语言代码。

使用最广泛的语言的语言代码示例：

- 英文 - en
- 简体中文 - zh-CN
- 俄语 - ru
- 韩语 - ko
- 波兰语 - pl
- 乌克兰语 - uk

## 外部文章标题

一些字符串包含外部文章的标题。 我们的大多数开发人员文档页面都包含指向外部文章的链接，以供进一步阅读。 无论文章的语言如何，都需要翻译包含文章标题的字符串，以确保以他们的语言查看页面的访问者获得更一致的用户体验。

## Crowdin 警告

Crowdin 有一个内置功能，可以在翻译人员即将出错时发出警告。 在保存翻译之前，如果你忘记在译文中加上原文中的标签、翻译了不应翻译的元素、添加了多个连续的空格、忘记结尾标点等，Crowdin 会自动提醒你。 如果你看到这样的警告，请返回并仔细检查建议的翻译。

:::warning
永远不要忽略这些警告，因为它们通常意味着有问题，或者翻译缺少源文本的关键部分。
:::

## 简短与完整形式/缩写

网站上使用了很多缩写，例如 dApp、NFT、DAO、DeFi 等。 这些缩写通常用于英语，并且大多数网站访问者都熟悉它们。

由于它们通常没有其他语言的既定翻译，处理这些和类似术语的最佳方法是提供完整形式的描述性翻译，并在括号中添加英文缩写。

不要翻译这些缩写，因为大多数人不熟悉它们，而且本地化版本对大多数访问者来说没有多大意义。

如何翻译 dApp 的示例：

- Decentralized applications (dapps) → 完整的翻译形式 (括号中为英文缩写)

## 没有既定翻译的术语

某些术语在其他语言中可能没有既定翻译，并且以原始英语术语而广为人知。 这些术语主要包括较新的概念，如工作量证明、权益证明、信标链、质押等。

虽然翻译这些术语听起来不自然，但由于英文版本也常用于其他语言，因此强烈建议将它们翻译。

翻译它们时，请随意发挥创意，使用描述性翻译，或直接按字面翻译。

**大多数术语应该翻译而不是将其中一些保留英文的原因是，随着越来越多的人开始使用TON和相关技术，这种新术语将在未来变得更加普遍。 如果我们想让来自世界各地的更多人加入这个领域，我们需要以尽可能多的语言提供易于理解的术语，即使我们需要自行创建它。**

## 按钮与行动号召

网站包含许多按钮，其翻译方式应与其他内容不同。

可以通过查看上下文屏幕截图、与大多数字符串连接或通过检查编辑器中的上下文（包括短语“button”）来识别按钮文本。

按钮的翻译应尽可能简短，以防止格式不匹配。 此外，按钮翻译应该是必要的，即呈现命令或请求。

## 翻译包容性

TON 文档的访问者来自世界各地和不同的背景。 因此，网站上的语言应该是中立的，欢迎所有人而不是排他性的。

其中一个重要方面是性别中立。 这可以通过使用正式的地址形式并避免在翻译中使用任何特定性别的词来轻松实现。

另一种形式的包容性是，尝试面向全球观众翻译，而不是面向任何国家、种族或地区。

最后，语言应该适合所有大众和年龄段的读者。

## 特定语言的翻译

翻译时，重要的是要遵循你的语言中使用的语法规则、约定和格式，而不是从源复制。 源文本遵循英语语法规则和约定，而这不适用于许多其他语言。

你应该了解你的语言规则并进行相应的翻译。 如果你需要帮助，请与我们联系，我们将帮助你找到一些有关如何在你的语言中使用这些元素的资源。

一些需要特别注意的例子：

### 标点、格式

#### 大写

- 不同语言的大小写存在巨大差异。
- 在英语中，通常将标题和名称、月份和日期、语言名称、假期等中的所有单词大写。 在许多其他语言中，这在语法上是不正确的，因为它们具有不同的大小写规则。
- 一些语言也有关于人称代词、名词和某些形容词大写的规则，这些在英语中是不大写的。

#### 间距

- 正字法规则定义了每种语言的空格使用。 因为到处都使用空格，所以这些规则是最独特的，而空格是最容易误译的元素。
- 英语和其他语言之间的一些常见间距差异：
  - 计量单位和货币前的空格（例如 USD、EUR、kB、MB）
  - 度数符号前的空格（例如°C、℉）
  - 一些标点符号前的空格，尤其是省略号 (...)
  - 斜杠前后的空格 (/)

#### 列表

- 每种语言都有一套多样化和复杂的规则来编写列表。 这些可能与英语有很大不同。
- 在某些语言中，每个新行的第一个单词需要大写，而在其他语言中，新行应该以小写字母开头。 许多语言对列表中的大小写也有不同的规则，具体取决于每行的长度。
- 这同样适用于行项目的标点符号。 列表中的结束标点可以是句点 (.)、逗号 (,) 或分号 (；)具体取决于语言

#### 引号

- 语言使用许多不同的引号。 简单地从源中复制英文引号通常是不正确的。
- 一些最常见的引号类型包括：
  - “示例文本”
  - ‘示例文本’
  - »示例文本«
  - “示例文本”
  - ‘示例文本’
  - «示例文本»

#### 连字符和破折号

- 在英语中，连字符 (-) 用于连接单词或单词的不同部分，而破折号 (-) 用于表示范围或停顿。
- 许多语言对使用连字符和破折号有不同的规则，应遵守这些规则。

### 格式

#### 数字

- 用不同语言书写数字的主要区别在于用于小数和千位的分隔符。 对于千数来说，这可以是句号、逗号或空格。 同样，一些语言使用小数点，而另一些语言使用小数点逗号。
  - 一些大数的例子：
    - 英语 - 1,000.50
    - 西班牙语 - 1.000,50
    - 法语 - 1 000,50
- 翻译数字时的另一个重要考虑因素是百分号。 它可以用不同的方式编写：100%、100 % 或 %100。
- 最后，负数可以不同地显示，具体取决于语言：-100、100-、(100) 或 [100]。

#### 日期

- 在翻译日期时，有许多基于语言的考虑因素和差异。 这些包括日期格式、分隔符、大写和前导零。 全长日期和数字日期之间也存在差异。
  - 不同日期格式的一些示例：
    - 英语（英国）(dd/mm/yyyy) – 1st January, 2022
    - 英语（美国）(mm/dd/yyyy) – January 1st, 2022
    - 中文 (yyyy-mm-dd) – 2022 年 1 月 1 日
    - 法语 (dd/mm/yyyy) – 1er janvier 2022
    - 意大利语 (dd/mm/yyyy) – 1º gennaio 2022
    - 德语 (yyyy/mm/dd) – 1. Januar 2022

#### 货币

- 由于格式、惯例和转换不同，货币转换可能具有挑战性。 作为一般规则，请保持货币与来源相同。 为了读者的利益，你可以在括号中添加你的当地货币和转换。
- 用不同语言书写货币的主要区别包括符号位置、小数逗号与小数点、间距以及缩写与符号。
  - 符号放置：美元 100或 100 美元
  - 小数逗号和。小数点：100,50$ 或 100.50$
  - 间距：100美元或 100 美元
  - 缩写和符号：100$ 或 100 USD

#### 计量单位

- 作为一般规则，请根据来源保留计量单位。 如果你所在的国家/地区使用不同的系统，你可以将转换包括在括号中。
- 除了度量单位的本地化之外，注意语言处理这些单位的方式的差异也很重要。 主要区别在于数字和单位之间的间距，可以根据语言而有所不同。 这方面的示例包括 100kB 与 100 kB 或 50ºF 与 50ºF。

## 结论

翻译时尽量不要着急。 放轻松，玩得开心！

感谢你参与翻译计划并帮助我们让更广泛的受众可以访问网站。 TON社区是全球性的，我们很高兴你也成为其中的一员！
