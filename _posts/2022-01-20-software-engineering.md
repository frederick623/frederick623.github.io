---
layout: post
title:  "點解software engineering咁難？"
date:   2022-01-20 12:20:00 +08:00
categories: [programming]
---
![image](/assets/img/Tiramisu_-_Raffaele_Diomede.jpg)

最近生活有個經驗正正反映software engineering之難處。

話說家有喜慶，想買嘢慶祝：

「不如買去Cova買個Tiramisu？」

{% highlight python}
class Cova:
	class Flavor:
        Tiramisu = "tiramisu"
        Strawberry = "strawberry"
        Mango = "mango"

	Cova(flavor)

def purchase_present(cova):
    ...
    return

def main():
	my_cova = Cova(Cova.Flavor.Tiramisu)
	purchase_present(my_cova)

{% endhighlight %}

買過幾次相安無事，某日：

「唔係喎，IFC間Cova執咗喎。」

「咁第間啦，Italian Tomato揀隻cheesecake啦。」

class Cake
{
}

class Cova(Cake):
	class Flavor:
        Tiramisu = "tiramisu"
        Strawberry = "strawberry"
        Mango = "mango"

class ItalianTomato(Cake):
	class Flavor:
        Chestnut = "chestnut"
        Strawberry = "strawberry"

def purchase_present(cake):
    ...
    return

def main():
	my_cake = ItalianTomato(ItalianTomato.Flavor.Chestnut)
	purchase_present(my_cake)

到某日，原來食蛋糕都會有食到厭既一日，又變成⋯⋯

class Gift:
    ...

class Cake(Gift):
    ...

class Toy(Gift):
    ...

...

由以上例子可以見到，基本上定下框架（framework）時，有幾concrete或幾abstract，又是另一個學問。譬如因為當初user定下requirements，只想食tiramisu，就完全無視有其他蛋糕之可能性，固然目光狹窄；相反，一開始就目光過份遠大，定下整個由gift開始的class inheritance，不免overdone。

因此，software engineer係需要有一定程度的預知未來能力，如果無，最少也要有幾分common sense。
