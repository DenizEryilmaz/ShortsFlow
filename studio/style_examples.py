"""Curated 20-second (4x5s) example projects for every visual style in ShortsFlow."""

STYLE_EXAMPLES = {
    'animation_2d': {
        'name': 'Son Fenerin Işığı (2D Animasyon Örneği)',
        'brief': 'Fırtınalı bir gecede eski deniz fenerini yeniden yakan yaşlı bekçinin, kayıp bir tekneye yol göstermesi.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'warm_story',
        'transition': 'crossfade',
        'caption_style': 'shorts',
        'script': {
            'title': 'Son Fenerin Işığı',
            'logline': 'Fırtınalı bir gecede sönen deniz fenerini yeniden yakan yaşlı bekçi, kayıp bir tekneye eve dönüş yolunu açar.',
            'continuity_note': 'Aynı taş deniz feneri, fırtınalı koyu lacivert gökyüzü ve sıcak kehribar fener ışığı korunmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Fırtınadaki Fener',
                    'duration': 5,
                    'narration': 'Fırtına büyüdükçe kıyıdaki eski fenerin ışığı titremeye başladı.',
                    'caption': 'Fırtınada titreyen ışık.',
                    'shot_size': 'establishing',
                    'camera_move': 'push',
                    'visual_prompt': 'Tall weathered stone lighthouse on a dark rocky cliff at night, heavy rain streaks and crashing sea foam below, faint flickering amber light inside the top lantern room.',
                    'end_prompt': 'Closer view of the same stone lighthouse as a sudden gust of wind extinguishes the lantern light into deep blue darkness.',
                    'motion_prompt': 'Slow cinematic push-in toward the lighthouse tower while rain lashes diagonally and ocean waves crash against the rocks as the top light flickers out.',
                    'negative_prompt': 'text, watermark, modern boats, daylight',
                },
                {
                    'id': 'scene-02',
                    'title': 'Rüzgâra Karşı Kıvılcım',
                    'duration': 5,
                    'narration': 'Yaşlı bekçi, ıslak basamakları çıkıp kibritini rüzgâra siper etti.',
                    'caption': 'Rüzgâra karşı tek kıvılcım.',
                    'shot_size': 'medium',
                    'camera_move': 'tilt_up',
                    'visual_prompt': 'Inside the cramped stone lantern room, an elderly lighthouse keeper in a yellow oilskin coat shields a wooden match with cupped weathered hands next to a large brass oil lamp.',
                    'end_prompt': 'The match flares brightly in the keeper hands, casting warm golden light across his determined face and the gleaming brass lamp.',
                    'motion_prompt': 'Gentle upward tilt as the elderly keeper strikes the match, cupping his hands protectively while the warm flame catches and illuminates his face.',
                    'negative_prompt': 'text, watermark, extra people, modern flashlight',
                },
                {
                    'id': 'scene-03',
                    'title': 'Altın Hüzme',
                    'duration': 5,
                    'narration': 'Bakır fener alev alınca altın bir hüzme karanlığı yardı.',
                    'caption': 'Karanlığı yaran altın ışık.',
                    'shot_size': 'closeup',
                    'camera_move': 'static',
                    'visual_prompt': 'Close-up of the ornate brass Fresnel lens inside the lighthouse beginning to glow with a rich golden flame, rain droplets beading on the glass panes.',
                    'end_prompt': 'The Fresnel lens blazes at full brilliance, projecting a powerful sweeping golden beam out through the rainy night sky.',
                    'motion_prompt': 'Fixed dramatic camera as the brass lamp ignites fully and the Fresnel lens begins rotating, sending a radiant golden beam cutting through the rain.',
                    'negative_prompt': 'text, watermark, blurry',
                },
                {
                    'id': 'scene-04',
                    'title': 'Eve Dönüş',
                    'duration': 5,
                    'narration': 'Uzaktaki küçük tekne ışığı gördü ve güvenle limana döndü.',
                    'caption': 'Eve dönen yol bulundu.',
                    'shot_size': 'wide',
                    'camera_move': 'pull',
                    'visual_prompt': 'Wide coastal view from above the dark sea, a small wooden fishing boat tossing on the waves as the lighthouse golden beam sweeps across the water toward it.',
                    'end_prompt': 'The small wooden boat steers steadily along the golden reflection on calmer water toward the warm glowing harbor lights below the lighthouse.',
                    'motion_prompt': 'Slow sweeping pull-back as the lighthouse beam guides the little boat across the dark sea toward the safe glowing harbor.',
                    'negative_prompt': 'text, watermark, modern cruise ship',
                },
            ],
        },
    },
    'paint_storybook': {
        'name': 'Bulutları Toplayan Çocuk (Masal Kitabı Örneği)',
        'brief': 'Kurak bir köyde tepeden küçük bir pamuk bulutu kavanoza doldurup bahçelere yağmur getiren çocuğun masalı.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'warm_story',
        'transition': 'crossfade',
        'caption_style': 'classic',
        'script': {
            'title': 'Bulutları Toplayan Çocuk',
            'logline': 'Kurak bir yazda tepedeki tek küçük bulutu kavanoza çağıran Defne, köyün bahçelerine yeniden hayat verir.',
            'continuity_note': 'Defne kırmızı örgülü hırkası ve cam kavanozuyla tüm sahnelerde aynı sıcak suluboya palette kalmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Susuz Köy',
                    'duration': 5,
                    'narration': 'Yaz çok uzun sürdü, köyün bütün çiçekleri boynunu büktü.',
                    'caption': 'Yağmuru bekleyen köy.',
                    'shot_size': 'wide',
                    'camera_move': 'pan_right',
                    'visual_prompt': 'Sun-baked hilltop village with cozy wooden cottages, dry ochre earth, and drooping sunflowers under a pale golden summer sky.',
                    'end_prompt': 'A small girl in a knitted red cardigan stands at the edge of the dry garden holding an empty glass jar, looking up toward a distant green hill.',
                    'motion_prompt': 'Gentle watercolor pan to the right across the drooping village gardens, settling on the little girl gazing upward with her empty glass jar.',
                    'negative_prompt': 'text, watermark, photorealistic, modern cars',
                },
                {
                    'id': 'scene-02',
                    'title': 'Kavanozdaki Bulut',
                    'duration': 5,
                    'narration': 'Küçük Defne tepedeki en yumuşak bulutu cam kavanoza çağırdı.',
                    'caption': 'Kavanozdaki küçük bulut.',
                    'shot_size': 'medium',
                    'camera_move': 'push',
                    'visual_prompt': 'On a breezy meadow hilltop, the little girl in a red cardigan holds up an open glass jar toward a tiny fluffy white cotton cloud floating low above the grass.',
                    'end_prompt': 'The miniature fluffy cloud curls gently inside the glass jar, glowing softly as the girl smiles and closes the cork lid.',
                    'motion_prompt': 'Slow warm push-in as the soft little cloud drifts playfully down into the open glass jar while tall grass sways in the breeze.',
                    'negative_prompt': 'text, watermark, dark storm',
                },
                {
                    'id': 'scene-03',
                    'title': 'Gümüş Damlalar',
                    'duration': 5,
                    'narration': 'Köye inip kapağı açınca gümüş damlalar toprağa döküldü.',
                    'caption': 'İlk gümüş damlalar.',
                    'shot_size': 'closeup',
                    'camera_move': 'tilt_down',
                    'visual_prompt': 'Close-up of the girl hands uncorking the glass jar above a parched flowerbed, the tiny cloud rising out and releasing sparkling silver raindrops.',
                    'end_prompt': 'Cool sparkling raindrops splash onto the dry soil and thirsty petals, turning the earth rich and dark.',
                    'motion_prompt': 'Soft downward tilt following the shimmering raindrops as they fall from the little cloud onto the dry petals and dark soil.',
                    'negative_prompt': 'text, watermark, harsh lighting',
                },
                {
                    'id': 'scene-04',
                    'title': 'Uyanan Bahçeler',
                    'duration': 5,
                    'narration': 'Dakikalar içinde kuru bahçeler yeniden renklerle dolup taştı.',
                    'caption': 'Bahçeler yeniden uyandı.',
                    'shot_size': 'establishing',
                    'camera_move': 'pull',
                    'visual_prompt': 'The village gardens bursting into vibrant watercolor blooms of yellow, coral, and green under a gentle rainbow mist while the little girl spins joyfully.',
                    'end_prompt': 'Wide storybook panorama of the blooming colorful hillside village under warm sunlit clouds and a soft rainbow.',
                    'motion_prompt': 'Graceful slow pull-back revealing the entire village blooming back to life with bright flowers and floating mist.',
                    'negative_prompt': 'text, watermark, dreary colors',
                },
            ],
        },
    },
    'science_2d': {
        'name': 'Güneşten Gelen 8 Dakika (Bilim Animasyonu Örneği)',
        'brief': 'Bir fotonun Güneş yüzeyinden çıkıp uzay boşluğunu aşarak sekiz dakika yirmi saniyede Dünya ya ulaşması.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'science_pulse',
        'transition': 'cut',
        'caption_style': 'shorts',
        'script': {
            'title': 'Güneşten Gelen 8 Dakika',
            'logline': 'Güneş yüzeyinden kopan bir ışık taneciğinin 150 milyon kilometrelik yolculuğunu 20 saniyede keşfedin.',
            'continuity_note': 'Koyu petrol mavisi uzay arka planı, sıcak turuncu Güneş ve parlak altın foton taneciği tutarlı kalmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Sekiz Dakika Önceki Güneş',
                    'duration': 5,
                    'narration': 'Güneş’e baktığında aslında sekiz dakika önceki halini görürsün.',
                    'caption': '8 dakika önceki Güneş.',
                    'shot_size': 'closeup',
                    'camera_move': 'push',
                    'visual_prompt': 'Stylized educational 2D cross-section of the glowing orange Sun surface against a deep teal space backdrop, a single bright golden photon sphere detaching from a solar flare.',
                    'end_prompt': 'The bright golden photon sphere breaks free into the dark teal space, leaving a clean glowing ripple on the Sun edge.',
                    'motion_prompt': 'Smooth push-in as the glowing golden photon pulses and launches cleanly off the orange solar surface into space.',
                    'negative_prompt': 'text, labels, numbers, watermark',
                },
                {
                    'id': 'scene-02',
                    'title': 'Işık Hızı',
                    'duration': 5,
                    'narration': 'Bir ışık taneciği saniyede üç yüz bin kilometre hızla uçar.',
                    'caption': '300.000 km/sn hız.',
                    'shot_size': 'wide',
                    'camera_move': 'tracking',
                    'visual_prompt': 'The glowing golden photon streaking rapidly from left to right across deep teal space, trailing crisp luminous speed lines past tiny distant stars.',
                    'end_prompt': 'The photon zips past stylized small silhouettes of Mercury and Venus along clean orbital arcs.',
                    'motion_prompt': 'Fast smooth tracking camera following the golden photon gliding effortlessly past clean geometric planet orbits.',
                    'negative_prompt': 'text, letters, watermark, cluttered',
                },
                {
                    'id': 'scene-03',
                    'title': 'Sessiz Boşluk',
                    'duration': 5,
                    'narration': 'Yüz elli milyon kilometrelik boşluğu durmadan, sessizce aşar.',
                    'caption': '150 milyon km yolculuk.',
                    'shot_size': 'medium',
                    'camera_move': 'pan_right',
                    'visual_prompt': 'Clean geometric diagram view of deep teal space showing the small orange Sun on the far left and a crisp blue-and-green Earth appearing on the far right, connected by a delicate dotted arc.',
                    'end_prompt': 'The golden photon nears the curved turquoise atmosphere of Earth on the right side of the frame.',
                    'motion_prompt': 'Steady pan to the right tracking the bright golden photon traveling smoothly along the dotted arc toward Earth.',
                    'negative_prompt': 'text, numbers, watermark',
                },
                {
                    'id': 'scene-04',
                    'title': 'Geçmişten Gelen Mektup',
                    'duration': 5,
                    'narration': 'Gözüne ulaştığında gökyüzü, geçmişten gelen canlı bir mektuptur.',
                    'caption': 'Geçmişten gelen ışık.',
                    'shot_size': 'establishing',
                    'camera_move': 'pull',
                    'visual_prompt': 'A peaceful sunlit meadow on Earth as warm golden sunbeams touch green leaves and a curious observer looking up at the bright morning sky.',
                    'end_prompt': 'Wide serene view of the sunlit hillside glowing with warm golden rays radiating down from the bright sky.',
                    'motion_prompt': 'Gentle pull-back as warm golden rays wash over the meadow and leaves sway softly in the morning light.',
                    'negative_prompt': 'text, watermark, dark night',
                },
            ],
        },
    },
    'paper_cut': {
        'name': 'Kâğıttan İlk Kitap (Paper-Cut Örneği)',
        'brief': 'Bir matbaa atölyesinde tek tek dizilen harflerin mürekkeple buluşup dünyaya yayılan sayfalara dönüşmesi.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'calm_ambient',
        'transition': 'fade',
        'caption_style': 'classic',
        'script': {
            'title': 'Kâğıttan İlk Kitap',
            'logline': 'Katmanlı kâğıt kesimi estetiğiyle matbaanın doğuşu ve bilginin dünyaya yayılış hikâyesi.',
            'continuity_note': 'Lifli krem, bordo, koyu petrol ve kahverengi kâğıt katmanları ile gerçekçi gölgeler korunmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Elle Yazılan Yıllar',
                    'duration': 5,
                    'narration': 'Eskiden tek bir kitabı yazmak aylar, hatta yıllar sürerdi.',
                    'caption': 'Aylar süren tek kitap.',
                    'shot_size': 'medium',
                    'camera_move': 'push',
                    'visual_prompt': 'Layered cut-paper scene of a candlelit medieval desk with a single thick parchment book, a paper feather quill, and warm cast shadows between textured paper layers.',
                    'end_prompt': 'Closer view of the desk showing stacks of blank fibrous cream paper waiting beside the glowing paper candle flame.',
                    'motion_prompt': 'Slow stop-motion push-in toward the candlelit desk as the paper flame flickers softly and shadows shift gently.',
                    'negative_prompt': 'text, watermark, 3D plastic, glossy',
                },
                {
                    'id': 'scene-02',
                    'title': 'Metal Harfler',
                    'duration': 5,
                    'narration': 'Ta ki küçük metal harfler yan yana dizilip mürekkeplenene kadar.',
                    'caption': 'Mürekkep ve metal harfler.',
                    'shot_size': 'closeup',
                    'camera_move': 'pan_right',
                    'visual_prompt': 'Top-down layered cut-paper tray filled with neat miniature slate-colored letter blocks arranged in tidy rows, deep paper shadows around every block.',
                    'end_prompt': 'A dark ink roller made of layered charcoal paper glides smoothly across the neat rows of letter blocks.',
                    'motion_prompt': 'Smooth horizontal pan to the right following the dark paper ink roller passing evenly over the neat rows of blocks.',
                    'negative_prompt': 'readable modern words, watermark, blurry',
                },
                {
                    'id': 'scene-03',
                    'title': 'İlk Basılı Sayfa',
                    'duration': 5,
                    'narration': 'Ahşap baskı kolu indi ve ilk temiz sayfa hayat buldu.',
                    'caption': 'İlk basılı sayfa.',
                    'shot_size': 'medium',
                    'camera_move': 'tilt_down',
                    'visual_prompt': 'An artisan wooden printing press crafted from rich brown and crimson layered cut paper inside a cozy workshop, warm side lighting casting crisp shadows.',
                    'end_prompt': 'The wooden press lever lowers and lifts to reveal a crisp cream printed sheet rising from the press bed.',
                    'motion_prompt': 'Subtle downward tilt in tactile stop-motion rhythm as the press arm lowers and a fresh cream sheet emerges.',
                    'negative_prompt': 'text, watermark, modern machinery',
                },
                {
                    'id': 'scene-04',
                    'title': 'Dünyaya Yayılan Bilgi',
                    'duration': 5,
                    'narration': 'O günden sonra bilgi, tek bir masadan bütün dünyaya uçtu.',
                    'caption': 'Dünyaya yayılan bilgi.',
                    'shot_size': 'wide',
                    'camera_move': 'pull',
                    'visual_prompt': 'Dozens of folded cream paper pages shaped like graceful birds lifting off from the wooden workshop table toward a starry teal cut-paper sky.',
                    'end_prompt': 'Wide layered diorama of paper pages soaring over miniature paper rooftops and hills into the glowing horizon.',
                    'motion_prompt': 'Slow majestic pull-back as flocks of folded paper pages glide upward and outward across the layered paper skyline.',
                    'negative_prompt': 'text, watermark, cluttered',
                },
            ],
        },
    },
    'anime_cel': {
        'name': 'Son Trenin Penceresi (Anime Cel Örneği)',
        'brief': 'Gün batımında kıyıdan geçen son trende pencere kenarında oturan gencin, geçip giden yazı izlemesi.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'calm_ambient',
        'transition': 'crossfade',
        'caption_style': 'minimal',
        'script': {
            'title': 'Son Trenin Penceresi',
            'logline': 'Gün batımında deniz kıyısından süzülen trende, rüzgâr ve ışık eşliğinde huzurlu bir yaz akşamı.',
            'continuity_note': 'Turuncu-pembe gün batımı gökyüzü, klasik yeşil-krem banliyö treni ve temiz anime cel çizgileri korunmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Kıyıdaki Son Tren',
                    'duration': 5,
                    'narration': 'Gün batarken kıyı treni turuncu bulutların altından süzülüyordu.',
                    'caption': 'Gün batımında son tren.',
                    'shot_size': 'wide',
                    'camera_move': 'tracking',
                    'visual_prompt': 'Classic Japanese-style commuter train gliding along a coastal rail embankment beside a sparkling sunset sea, towering orange and rose cumulus clouds filling the sky.',
                    'end_prompt': 'The train curves gently along the coastline as golden sunset light glints off its windows and overhead wires.',
                    'motion_prompt': 'Smooth cinematic tracking shot gliding alongside the coastal train as ocean waves sparkle and sunset clouds drift slowly.',
                    'negative_prompt': 'text, watermark, 3D CGI, muddy lines',
                },
                {
                    'id': 'scene-02',
                    'title': 'Rüzgârla Çevrilen Sayfalar',
                    'duration': 5,
                    'narration': 'Pencereden esen ılık rüzgâr defterin sayfalarını yavaşça çevirdi.',
                    'caption': 'Rüzgârla çevrilen sayfalar.',
                    'shot_size': 'closeup',
                    'camera_move': 'static',
                    'visual_prompt': 'Inside the quiet train car bathed in warm golden hour light, an open sketchbook resting on a wooden lap beside an open train window, soft breeze lifting a page corner.',
                    'end_prompt': 'The sketchbook pages flutter gently in the warm breeze while orange sunlight dances across the empty seats.',
                    'motion_prompt': 'Fixed peaceful anime camera as warm air from the open window softly turns the sketchbook pages and dust motes float in sunbeams.',
                    'negative_prompt': 'text, watermark, crowded train',
                },
                {
                    'id': 'scene-03',
                    'title': 'Uyanan Şehir Işıkları',
                    'duration': 5,
                    'narration': 'Uzakta deniz parlıyor, şehir ışıkları birer birer yanıyordu.',
                    'caption': 'Uyanan şehir ışıkları.',
                    'shot_size': 'medium',
                    'camera_move': 'pan_left',
                    'visual_prompt': 'View from inside the train window looking out at a coastal town at twilight, deep cobalt sky meeting an amber horizon as warm house windows begin twinkling.',
                    'end_prompt': 'Clusters of warm yellow town lights reflect across the calm dark blue bay while telephone poles pass in silhouette.',
                    'motion_prompt': 'Gentle pan to the left across the train window frame as passing poles sweep by and warm evening lights flicker on across the bay.',
                    'negative_prompt': 'text, watermark, harsh neon',
                },
                {
                    'id': 'scene-04',
                    'title': 'Nefes Almak İçin Yolculuk',
                    'duration': 5,
                    'narration': 'Bazı yolculuklar bir yere varmak için değil, nefes almak içindir.',
                    'caption': 'Nefes almak için yolculuk.',
                    'shot_size': 'establishing',
                    'camera_move': 'pull',
                    'visual_prompt': 'Silhouetted young traveler resting their chin peacefully near the glowing train window as the train crosses a long bridge over the twilight sea.',
                    'end_prompt': 'Wide serene shot of the illuminated train gliding quietly across the bridge beneath the first evening stars.',
                    'motion_prompt': 'Slow lyrical pull-back from the glowing train car into a wide twilight panorama of the sea bridge and starry sky.',
                    'negative_prompt': 'text, watermark, busy foreground',
                },
            ],
        },
    },
    'clay_stopmotion': {
        'name': 'Minyatür Fırıncının Sabahı (Kil Stop-Motion Örneği)',
        'brief': 'Şafak sökerken küçük atölyesinde hamur yoğurup fırından sıcacık ekmek çıkaran minyatür kil fırıncı.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'warm_story',
        'transition': 'cut',
        'caption_style': 'shorts',
        'script': {
            'title': 'Minyatür Fırıncının Sabahı',
            'logline': 'Parmak izi dokulu el yapımı kil dünyasında, şafak vakti tüm kasabayı ekmek kokusuyla uyandıran minyatür fırıncı.',
            'continuity_note': 'Sıcak stüdyo ışığı, el yapımı parmak izi dokulu kil yüzeyler ve sığ alan derinliği korunmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Şafakta Uyanan Fırın',
                    'duration': 5,
                    'narration': 'Kasaba hâlâ uyurken küçük fırının bacasından ilk duman yükseldi.',
                    'caption': 'Şafakta uyanan fırın.',
                    'shot_size': 'establishing',
                    'camera_move': 'push',
                    'visual_prompt': 'Miniature handcrafted clay diorama of a cobblestone village street at cool blue dawn, one cozy terracotta bakery glowing warmly from its tiny window, a puff of cotton smoke above the chimney.',
                    'end_prompt': 'Closer view of the glowing bakery window with a tiny sculpted bread sign swaying gently in the morning air.',
                    'motion_prompt': 'Gentle stop-motion push-in toward the warmly lit miniature clay bakery as soft cotton-wool smoke puffs upward from the chimney.',
                    'negative_prompt': 'text, watermark, glossy plastic, photorealistic human',
                },
                {
                    'id': 'scene-02',
                    'title': 'Un Bulutunda Hamur',
                    'duration': 5,
                    'narration': 'Minik eller un bulutunun içinde yumuşacık hamuru özenle yoğurdu.',
                    'caption': 'Un bulutunda hamur.',
                    'shot_size': 'closeup',
                    'camera_move': 'static',
                    'visual_prompt': 'Close-up of a chubby cheerful clay baker in a tiny white apron and hat kneading a round lump of cream-colored clay dough on a miniature wooden table dusted with flour.',
                    'end_prompt': 'A playful puff of white flour rises in the warm key light as the baker shapes the dough into a neat round loaf.',
                    'motion_prompt': 'Fixed tactile stop-motion camera capturing the tiny clay hands pressing and folding the dough rhythmically with tiny puffs of flour.',
                    'negative_prompt': 'text, watermark, real human hands',
                },
                {
                    'id': 'scene-03',
                    'title': 'Altın Kabuklu Ekmekler',
                    'duration': 5,
                    'narration': 'Taş fırının kapağı açılınca altın kabuklu ekmekler göründü.',
                    'caption': 'Altın kabuklu ekmekler.',
                    'shot_size': 'medium',
                    'camera_move': 'tilt_up',
                    'visual_prompt': 'Inside the tiny bakery, the clay baker pulls a miniature wooden peel out of a glowing brick oven holding two freshly baked golden-brown clay loaves.',
                    'end_prompt': 'Warm amber oven light illuminates the baker proud smiling face as delicate wisps of steam rise from the golden loaves.',
                    'motion_prompt': 'Gentle upward tilt as the baker slides the golden loaves out of the glowing oven and smiles proudly.',
                    'negative_prompt': 'text, watermark, burnt food',
                },
                {
                    'id': 'scene-04',
                    'title': 'Kasabayı Uyandıran Koku',
                    'duration': 5,
                    'narration': 'Taze ekmek kokusu sokağa yayıldı ve bütün kasaba gülümsedi.',
                    'caption': 'Kasabayı uyandıran koku.',
                    'shot_size': 'wide',
                    'camera_move': 'pull',
                    'visual_prompt': 'The miniature clay bakery door opens onto the sunlit cobblestone street, tiny clay villagers peeking happily out of nearby windows toward the warm bread shelf.',
                    'end_prompt': 'Wide sunlit miniature village square coming alive with warm morning light and happy clay neighbors gathering outside the bakery.',
                    'motion_prompt': 'Slow pull-back revealing the sunlit clay village waking up cheerfully around the cozy bakery.',
                    'negative_prompt': 'text, watermark, dark shadows',
                },
            ],
        },
    },
    'noir_comic': {
        'name': 'Yağmurlu Sokaktaki Anahtar (Noir Örneği)',
        'brief': 'Gece yarısı yağmurlu bir sokakta tek bir sokak lambasının altında parlak bir pirinç anahtar bulan dedektifin gizemi.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'calm_ambient',
        'transition': 'fade',
        'caption_style': 'minimal',
        'script': {
            'title': 'Yağmurlu Sokaktaki Anahtar',
            'logline': 'Siyah mürekkep gölgeleri ve tek bir kehribar lamba altında başlayan 20 saniyelik noir dedektif açılışı.',
            'continuity_note': 'Yüksek kontrastlı siyah mürekkep gölgeleri, yağmurlu kaldırım yansımaları ve kehribar ışık vurgusu korunmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Gece Yarısı Yağmuru',
                    'duration': 5,
                    'narration': 'Gece yarısı yağmur, şehrin bütün izlerini silmeye çalışıyordu.',
                    'caption': 'Gece yarısı yağmuru.',
                    'shot_size': 'establishing',
                    'camera_move': 'push',
                    'visual_prompt': 'High-contrast graphic novel alleyway at midnight, heavy ink rain pouring down through a single amber streetlamp cone, dramatic black shadows and wet cobblestone reflections.',
                    'end_prompt': 'A lone trench-coated silhouette with a fedora hat steps slowly into the pool of amber light on the rain-slicked alley.',
                    'motion_prompt': 'Slow moody push-in down the ink-black alley as rain streaks across the amber streetlamp glow and the detective enters frame.',
                    'negative_prompt': 'text, speech bubbles, watermark, bright daylight',
                },
                {
                    'id': 'scene-02',
                    'title': 'Kaldırımdaki İpucu',
                    'duration': 5,
                    'narration': 'Ama sokak lambasının altında parlayan küçük bir pirinç anahtar kaldı.',
                    'caption': 'Kaldırımdaki tek ipucu.',
                    'shot_size': 'closeup',
                    'camera_move': 'tilt_down',
                    'visual_prompt': 'Dramatic graphic novel close-up of a dark rain puddle on wet asphalt, a single ornate antique brass key glinting sharply in amber light amid falling ripples.',
                    'end_prompt': 'A gloved hand reaches down into the amber reflection to pick up the gleaming brass key from the puddle.',
                    'motion_prompt': 'Sharp downward tilt onto the rippling rain puddle as the gloved hand enters and lifts the bright brass key.',
                    'negative_prompt': 'text, speech bubbles, watermark',
                },
                {
                    'id': 'scene-03',
                    'title': 'Tanıdık Numara',
                    'duration': 5,
                    'narration': 'Dedektif anahtarı kaldırdı, üzerindeki eski numara tanıdıktı.',
                    'caption': 'Tanıdık bir oda numarası.',
                    'shot_size': 'medium',
                    'camera_move': 'pan_right',
                    'visual_prompt': 'Side profile of the trench-coated detective in dramatic amber rim lighting, holding the small brass key up near his eyes under the brim of his fedora, deep ink shadows across his face.',
                    'end_prompt': 'The detective lowers the key into his coat pocket and turns his gaze sharply toward a distant dimly lit hotel silhouette.',
                    'motion_prompt': 'Subtle pan to the right across the detective shadowed profile as he inspects the key and turns toward the distant building.',
                    'negative_prompt': 'text, speech bubbles, watermark, cheerful smile',
                },
                {
                    'id': 'scene-04',
                    'title': 'Açılan Dosya',
                    'duration': 5,
                    'narration': 'Gölgesini yağmura bırakıp kapanmamış dosyanın peşine düştü.',
                    'caption': 'Dosya yeniden açıldı.',
                    'shot_size': 'wide',
                    'camera_move': 'pull',
                    'visual_prompt': 'Wide graphic novel back view of the detective walking away down the wet noir street, his long black shadow stretching behind him toward the amber streetlamp.',
                    'end_prompt': 'The detective disappears into the misty rain-soaked city skyline while a single amber window glows high in the distance.',
                    'motion_prompt': 'Slow cinematic pull-back as the lone detective walks deeper into the rainy noir street toward the distant glowing window.',
                    'negative_prompt': 'text, speech bubbles, watermark',
                },
            ],
        },
    },
    'pixel_retro': {
        'name': 'Yıldız Kulesine Yolculuk (Retro Piksel Örneği)',
        'brief': 'Mor alacakaranlıkta küçük pikselli bir gezginin kamp ateşinden ayrılıp dağın zirvesindeki yıldız kulesini yakması.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'science_pulse',
        'transition': 'cut',
        'caption_style': 'shorts',
        'script': {
            'title': 'Yıldız Kulesine Yolculuk',
            'logline': '16-bit bağımsız oyun atmosferinde, mor dağların zirvesindeki yıldız fenerini uyandıran küçük gezginin hikâyesi.',
            'continuity_note': 'Keskin 16-bit piksel sanatı, mor-lacivert alacakaranlık gökyüzü ve sıcak altın ateş/yıldız ışıkları korunmalı.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Kamp Ateşinden Ayrılış',
                    'duration': 5,
                    'narration': 'Mor gökyüzünün altında küçük gezgin kamp ateşini geride bıraktı.',
                    'caption': 'Yolculuk başlıyor.',
                    'shot_size': 'wide',
                    'camera_move': 'pan_right',
                    'visual_prompt': '16-bit pixel art mountain cliff at purple twilight, a small cloaked pixel traveler with a backpack standing beside a crackling orange pixel campfire looking toward a tall distant mountain peak.',
                    'end_prompt': 'The small cloaked pixel traveler steps onto the winding stone trail heading right toward the dark pine forest and high peak.',
                    'motion_prompt': 'Crisp pixel-art pan to the right as campfire sparks rise and the tiny cloaked traveler sets off along the stone mountain trail.',
                    'negative_prompt': 'text, UI HUD, health bar, watermark, blurry',
                },
                {
                    'id': 'scene-02',
                    'title': 'Ateş Böceklerinin Işığı',
                    'duration': 5,
                    'narration': 'Taş patikadan tırmanırken ateş böcekleri yolunu aydınlattı.',
                    'caption': 'Ateş böceklerinin ışığı.',
                    'shot_size': 'medium',
                    'camera_move': 'tracking',
                    'visual_prompt': '16-bit pixel art forest path winding uphill under deep indigo pine trees, glowing golden pixel fireflies drifting around the tiny cloaked traveler climbing stone steps.',
                    'end_prompt': 'The traveler emerges above the pixel tree line onto a rocky ridge where an ancient stone tower stands silhouetted against the starry sky.',
                    'motion_prompt': 'Smooth side-scrolling tracking motion following the pixel traveler climbing the stone steps surrounded by twinkling golden fireflies.',
                    'negative_prompt': 'text, UI HUD, watermark, blurry',
                },
                {
                    'id': 'scene-03',
                    'title': 'Kristal Fener',
                    'duration': 5,
                    'narration': 'Zirvedeki eski kristal fener dokunuşuyla masmavi parladı.',
                    'caption': 'Kristal fener uyandı.',
                    'shot_size': 'closeup',
                    'camera_move': 'tilt_up',
                    'visual_prompt': '16-bit pixel art summit platform with a weathered stone pedestal holding a dormant cyan crystal lantern, the small cloaked traveler reaching out a hand toward the crystal.',
                    'end_prompt': 'The cyan crystal bursts with bright pixel starlight, sending a shimmering beam straight up into the purple night sky.',
                    'motion_prompt': 'Gentle upward tilt as the crystal lantern ignites into radiant pixel cyan light and sends sparkling pixels rising skyward.',
                    'negative_prompt': 'text, UI HUD, watermark, blurry',
                },
                {
                    'id': 'scene-04',
                    'title': 'Yeni Takımyıldızı',
                    'duration': 5,
                    'narration': 'Gökyüzünde yeni bir takımyıldızı belirdi, macera yeni başlıyordu.',
                    'caption': 'Macera yeni başlıyor.',
                    'shot_size': 'establishing',
                    'camera_move': 'pull',
                    'visual_prompt': 'Wide 16-bit pixel art mountain panorama at night, the tiny glowing cyan tower shining on the summit as bright pixel stars connect into a luminous golden constellation overhead.',
                    'end_prompt': 'Expansive nostalgic pixel sky filled with twinkling stars, drifting violet clouds, and the glowing mountain beacon below.',
                    'motion_prompt': 'Slow nostalgic pull-back revealing the glowing mountain summit and the sparkling golden constellation forming across the starry pixel sky.',
                    'negative_prompt': 'text, UI HUD, watermark, blurry',
                },
            ],
        },
    },
    'realistic_35mm': {
        'name': 'Gece Yarısı İtirafı (35mm Sinematik Örnek)',
        'brief': 'Yağmurlu bir gecede küçük bir İstanbul kafesinde iki eski arkadaş, yıllardır saklanan bir sırrı konuşur.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'calm_ambient',
        'transition': 'cut',
        'caption_style': 'minimal',
        'script': {
            'title': 'Gece Yarısı İtirafı',
            'logline': 'Yağmurlu bir gece kafesinde yıllar sonra buluşan iki eski dostun kısa ama gerilimli yüzleşmesi.',
            'continuity_note': 'Aynı yağmurlu cam kenarı masa, sıcak tungsten masa lambası, 35mm sinema film dokusu ve doğal cilt tonları.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Yağmurlu Kafe',
                    'scene_group': 'Sahne 1 · Kafe Buluşması',
                    'shot_mode': 'camera',
                    'duration': 5,
                    'narration': 'Yağmur camlara vururken kafede yalnızca köşe masanın ışığı yanıyordu.',
                    'caption': 'Köşe masada son ışık.',
                    'shot_size': 'establishing',
                    'camera_move': 'push',
                    'visual_prompt': 'Photorealistic 35mm cinema wide shot of a quiet rainy city cafe at night seen through rain-streaked glass, warm tungsten table lamp glowing in the corner booth, wet street reflections outside.',
                    'end_prompt': 'Closer view through the rain-beaded window toward the warm corner booth where two cups of tea steam softly.',
                    'motion_prompt': 'Slow steady dolly push-in toward the glowing cafe window as raindrops slide down the glass.',
                    'negative_prompt': 'cartoon, anime, 3D render, plastic skin, text, watermark',
                },
                {
                    'id': 'scene-02',
                    'title': 'Eski Zarf',
                    'scene_group': 'Sahne 1 · Kafe Buluşması',
                    'shot_mode': 'dialogue',
                    'duration': 5,
                    'narration': 'Bu zarfı beş yıl boyunca açmadan sakladım, artık gerçeği duymak istiyorum.',
                    'caption': 'Beş yıldır saklanan zarf.',
                    'shot_size': 'closeup',
                    'camera_move': 'static',
                    'visual_prompt': 'Photorealistic 35mm close-up portrait of a thoughtful woman in her thirties wearing a dark wool coat inside a warm tungsten-lit cafe at night, shallow depth of field, natural skin texture.',
                    'end_prompt': 'Same woman looking intently across the table in warm low-key cinema lighting.',
                    'motion_prompt': 'Subtle natural head movement and calm steady eye contact as she speaks quietly.',
                    'negative_prompt': 'cartoon, anime, CGI, plastic skin, text, watermark',
                },
                {
                    'id': 'scene-03',
                    'title': 'Karşı Açı',
                    'scene_group': 'Sahne 1 · Kafe Buluşması',
                    'shot_mode': 'dialogue',
                    'duration': 5,
                    'narration': 'O gece sana anlatamadım çünkü o mektup ikimizin de hayatını değiştirecekti.',
                    'caption': 'O gece anlatamadım.',
                    'shot_size': 'closeup',
                    'camera_move': 'static',
                    'visual_prompt': 'Photorealistic 35mm reverse-shot close-up of a bearded man in his thirties wearing a charcoal jacket sitting opposite in the same warm rainy cafe, soft bokeh city lights behind him.',
                    'end_prompt': 'Same man lowering his gaze thoughtfully in warm tungsten light.',
                    'motion_prompt': 'Subtle restrained facial expression and natural breathing as he answers honestly.',
                    'negative_prompt': 'cartoon, anime, CGI, plastic skin, text, watermark',
                },
                {
                    'id': 'scene-04',
                    'title': 'Masanın Üstündeki Karar',
                    'scene_group': 'Sahne 1 · Kafe Buluşması',
                    'shot_mode': 'action',
                    'duration': 5,
                    'narration': 'Zarfı masanın ortasına bıraktı ve ilk kez geriye dönüp bakmadı.',
                    'caption': 'Geriye dönüş yok.',
                    'shot_size': 'medium',
                    'camera_move': 'pull',
                    'visual_prompt': 'Photorealistic 35mm medium two-shot across a wooden cafe table, a weathered paper envelope resting beside two tea glasses under warm lamp light as rain falls outside the window.',
                    'end_prompt': 'Slightly wider shot showing the quiet rainy cafe as the envelope remains center frame on the table.',
                    'motion_prompt': 'Slow cinematic pull-back across the wooden table as steam curls softly from the tea glass.',
                    'negative_prompt': 'cartoon, anime, CGI, text, watermark',
                },
            ],
        },
    },
    'documentary_4k': {
        'name': 'Sabah Limanı (Belgesel Kamera Örneği)',
        'brief': 'Gün doğumunda küçük bir balıkçı limanında teknelerin denize açılma hazırlığı.',
        'duration': 20,
        'scene_count': 4,
        'bgm_preset': 'science_pulse',
        'transition': 'crossfade',
        'caption_style': 'minimal',
        'script': {
            'title': 'Sabah Limanı',
            'logline': 'Altın sabah ışığında kıyı balıkçılarının sakin ve gerçekçi gün doğumu hazırlığı.',
            'continuity_note': 'Doğal sabah güneşi, gerçekçi su yansımaları, 50mm belgesel kamerası ve doğal renkler.',
            'recommended_duration': 20,
            'episode_plan': [],
            'scenes': [
                {
                    'id': 'scene-01',
                    'title': 'Gün Doğumu Sisi',
                    'scene_group': 'Sahne 1 · Sabah Limanı',
                    'shot_mode': 'camera',
                    'duration': 5,
                    'narration': 'Şehir henüz uyanmamışken limanda ilk motor sesleri duyulmaya başlar.',
                    'caption': 'Şafakta ilk motor sesleri.',
                    'shot_size': 'establishing',
                    'camera_move': 'pan_right',
                    'visual_prompt': 'Authentic natural-light documentary wide shot of a quiet coastal fishing harbor at dawn, wooden fishing boats moored along a stone pier, soft golden sunrise mist over calm sea.',
                    'end_prompt': 'Harbor pier stretching toward the glowing horizon under soft morning light.',
                    'motion_prompt': 'Slow smooth horizontal pan across the calm harbor as golden sunlight touches the water.',
                    'negative_prompt': 'cartoon, CGI, over-saturated, text, watermark',
                },
                {
                    'id': 'scene-02',
                    'title': 'Ağların Hazırlığı',
                    'scene_group': 'Sahne 1 · Sabah Limanı',
                    'shot_mode': 'action',
                    'duration': 5,
                    'narration': 'Her sabah aynı sabırla ağlar kontrol edilir, halatlar tek tek toplanır.',
                    'caption': 'Sabırla hazırlanan ağlar.',
                    'shot_size': 'medium',
                    'camera_move': 'push',
                    'visual_prompt': 'Authentic documentary medium shot of weathered hands folding blue fishing nets on a wooden boat deck in crisp natural morning light, shallow depth of field.',
                    'end_prompt': 'Neatly coiled ropes and nets resting on the sunlit timber deck.',
                    'motion_prompt': 'Gentle steady push-in following the hands gathering the fishing net on the swaying deck.',
                    'negative_prompt': 'cartoon, CGI, plastic, text, watermark',
                },
                {
                    'id': 'scene-03',
                    'title': 'Kaptanın Bakışı',
                    'scene_group': 'Sahne 1 · Sabah Limanı',
                    'shot_mode': 'dialogue',
                    'duration': 5,
                    'narration': 'Deniz her gün farklı konuşur, rüzgârı dinlemeyi bilirsen yolunu bulursun.',
                    'caption': 'Rüzgârı dinlemeyi bilmek.',
                    'shot_size': 'closeup',
                    'camera_move': 'static',
                    'visual_prompt': 'Authentic documentary close-up portrait of a seasoned coastal fisherman in his fifties wearing a knit cap and navy jacket, warm sunrise light illuminating natural weathered skin, calm harbor background.',
                    'end_prompt': 'Same fisherman smiling subtly toward the horizon in golden morning light.',
                    'motion_prompt': 'Natural calm expression and gentle sea breeze moving his jacket collar.',
                    'negative_prompt': 'cartoon, CGI, plastic skin, text, watermark',
                },
                {
                    'id': 'scene-04',
                    'title': 'Açık Denize Doğru',
                    'scene_group': 'Sahne 1 · Sabah Limanı',
                    'shot_mode': 'camera',
                    'duration': 5,
                    'narration': 'Ve ilk tekne limandan ayrıldığında yeni bir gün resmen başlamış olur.',
                    'caption': 'Yeni gün başlıyor.',
                    'shot_size': 'wide',
                    'camera_move': 'pull',
                    'visual_prompt': 'Authentic documentary wide shot of a small wooden fishing boat gliding out of the stone harbor into shimmering golden morning sea, gentle white wake trailing behind.',
                    'end_prompt': 'The fishing boat moving further toward the bright open horizon over tranquil turquoise water.',
                    'motion_prompt': 'Slow pull-back as the boat glides smoothly across the shimmering water.',
                    'negative_prompt': 'cartoon, CGI, text, watermark',
                },
            ],
        },
    },
}


STYLE_EXAMPLES_EN = {
    'animation_2d': {
        'name': 'The Last Lighthouse (2D Animation Example)',
        'brief': 'On a stormy night, an elderly keeper relights an old coastal lighthouse to guide a lost fishing boat safely home.',
        'title': 'The Last Lighthouse',
        'logline': 'When a violent storm extinguishes the coastal lighthouse, an elderly keeper sparks a single flame to guide a lost boat home.',
        'continuity_note': 'Keep the same weathered stone lighthouse, dark stormy navy sky, and warm amber lantern glow across all scenes.',
        'scenes': [
            ('The Stormy Lighthouse', 'As the storm grew fierce, the old lighthouse beam began to flicker.', 'A flickering light in the storm.'),
            ('A Spark Against the Wind', 'The elderly keeper climbed the wet stairs and shielded a single match.', 'One spark against the wind.'),
            ('The Golden Beam', 'When the brass lamp caught fire, a golden beam cut through the dark.', 'Golden light pierces the night.'),
            ('Safe Return Home', 'Far out at sea, the little boat spotted the light and steered home.', 'The way home is found.'),
        ],
    },
    'paint_storybook': {
        'name': 'The Cloud Catcher (Storybook Example)',
        'brief': 'In a dry hilltop village, a young girl invites a soft little cloud into a glass jar to bring rain back to the gardens.',
        'title': 'The Cloud Catcher',
        'logline': 'After a long dry summer, young Defne catches a tiny cotton cloud in a glass jar to awaken her village gardens.',
        'continuity_note': 'Keep Defne in her knitted red cardigan with the corked glass jar in the same warm watercolor palette.',
        'scenes': [
            ('The Thirsty Village', 'Summer stretched too long, and every flower in the village hung its head.', 'A village waiting for rain.'),
            ('A Cloud in a Jar', 'Young Defne climbed the hill and invited a soft cloud into her jar.', 'A tiny cloud in glass.'),
            ('Silver Raindrops', 'Back in the garden, she opened the lid and silver drops fell softly.', 'The first silver raindrops.'),
            ('Gardens Awake', 'Within moments, the dry hillside burst back into bright summer color.', 'The gardens awaken again.'),
        ],
    },
    'science_2d': {
        'name': 'Eight Minutes from the Sun (Science 2D Example)',
        'brief': 'Follow a single photon leaving the Sun surface and racing 150 million kilometers through space to reach Earth.',
        'title': 'Eight Minutes from the Sun',
        'logline': 'Discover how a single particle of sunlight crosses 150 million kilometers of empty space in just eight minutes.',
        'continuity_note': 'Keep the deep teal space background, bright orange Sun, and crisp glowing golden photon consistent.',
        'scenes': [
            ('Eight Minutes Ago', 'When you look at the Sun, you actually see it eight minutes ago.', 'The Sun, 8 minutes ago.'),
            ('Speed of Light', 'A single photon races through space at three hundred thousand kilometers a second.', '300,000 km per second.'),
            ('Crossing the Void', 'It crosses one hundred fifty million kilometers of silence without stopping.', '150 million km journey.'),
            ('A Letter from the Past', 'By the time it reaches your eyes, sunlight is a message from the past.', 'Light from the past.'),
        ],
    },
    'paper_cut': {
        'name': 'The First Printed Page (Paper-Cut Example)',
        'brief': 'Inside a layered paper printshop, tiny metal letters meet dark ink and carry knowledge across the world.',
        'title': 'The First Printed Page',
        'logline': 'The birth of the printing press told through tactile fibrous paper layers and crisp stop-motion shadows.',
        'continuity_note': 'Preserve fibrous cream, crimson, slate, and deep teal cut-paper layers with realistic cast shadows.',
        'scenes': [
            ('Years by Hand', 'Long ago, copying a single book by hand took months or even years.', 'Months for one book.'),
            ('Ink and Metal Letters', 'Until tiny metal letters were lined up neatly and brushed with dark ink.', 'Metal letters and ink.'),
            ('The First Fresh Page', 'The wooden press lever came down, and the first crisp page came alive.', 'The first printed page.'),
            ('Knowledge Takes Flight', 'From that day on, ideas flew from one workshop to the entire world.', 'Knowledge spreads worldwide.'),
        ],
    },
    'anime_cel': {
        'name': 'Window of the Last Train (Anime Cel Example)',
        'brief': 'A quiet sunset ride on the last coastal train as warm breeze turns sketchbook pages and city lights wake up.',
        'title': 'Window of the Last Train',
        'logline': 'A peaceful twilight journey along the sea, bathed in orange clouds, warm wind, and waking town lights.',
        'continuity_note': 'Keep the orange-rose sunset sky, classic green-and-cream coastal train, and crisp hand-drawn cel lineart.',
        'scenes': [
            ('The Coastal Train', 'At sunset, the last coastal train glided beneath towering orange clouds.', 'Last train at sunset.'),
            ('Pages in the Breeze', 'A warm breeze from the open window softly turned the sketchbook pages.', 'Pages turned by the breeze.'),
            ('Waking Town Lights', 'Across the shimmering sea, warm town lights flickered on one by one.', 'City lights waking up.'),
            ('A Ride to Breathe', 'Some journeys are not meant to arrive, only to let you breathe.', 'A journey just to breathe.'),
        ],
    },
    'clay_stopmotion': {
        'name': 'The Miniature Baker Morning (Clay Stop-Motion Example)',
        'brief': 'At dawn, a handcrafted clay baker kneads dough in a cloud of flour and wakes the whole village with fresh bread.',
        'title': 'The Miniature Baker Morning',
        'logline': 'In a cozy handcrafted clay village, a tiny baker pulls golden loaves from a glowing oven at dawn.',
        'continuity_note': 'Keep fingerprint clay textures, miniature diorama scale, warm studio key light, and shallow depth of field.',
        'scenes': [
            ('Dawn at the Bakery', 'While the town still slept, the first wisp of smoke rose from the bakery.', 'A bakery wakes at dawn.'),
            ('Dough in a Flour Cloud', 'Tiny hands gently kneaded soft dough inside a playful cloud of flour.', 'Kneading in a flour cloud.'),
            ('Golden Crust Loaves', 'The stone oven opened to reveal two steaming, golden-brown loaves of bread.', 'Fresh golden loaves.'),
            ('The Scent That Woke Town', 'Warm bread scent drifted down the lane, and the whole village smiled.', 'A scent that wakes the town.'),
        ],
    },
    'noir_comic': {
        'name': 'The Key in the Rain (Noir Comic Example)',
        'brief': 'At midnight in a rain-soaked alley, a lone detective finds a gleaming brass key beneath a single amber streetlamp.',
        'title': 'The Key in the Rain',
        'logline': 'A 20-second graphic-novel noir opening in bold black ink, pouring rain, and a single amber streetlamp.',
        'continuity_note': 'Maintain high-contrast ink shadows, wet cobblestone reflections, and limited amber-and-slate palette.',
        'scenes': [
            ('Midnight Rain', 'At midnight, the pouring rain tried to wash away every trace in town.', 'Midnight rain in the alley.'),
            ('One Clue on the Curb', 'Yet one small brass key still glinted beneath the amber streetlamp.', 'A single clue remains.'),
            ('A Familiar Number', 'The detective lifted the key; the old room number felt strangely familiar.', 'A familiar room number.'),
            ('Case Reopened', 'Leaving his shadow in the rain, he stepped back into an unfinished case.', 'The case is open again.'),
        ],
    },
    'pixel_retro': {
        'name': 'Journey to Starlight Tower (Pixel Retro Example)',
        'brief': 'Under a purple twilight sky, a tiny cloaked pixel traveler leaves camp to ignite the ancient crystal beacon.',
        'title': 'Journey to Starlight Tower',
        'logline': 'A nostalgic 16-bit indie adventure following a small cloaked traveler climbing toward the mountain starlight beacon.',
        'continuity_note': 'Keep crisp 16-bit pixel art, purple-indigo twilight sky, and warm golden fire and starlight accents.',
        'scenes': [
            ('Leaving Campfire', 'Beneath a purple sky, the little traveler left the warm campfire behind.', 'The journey begins.'),
            ('Firefly Trail', 'Climbing the winding stone path, glowing fireflies lit every step ahead.', 'Guided by fireflies.'),
            ('The Crystal Beacon', 'At the summit, one touch awakened the ancient crystal in bright cyan light.', 'The crystal awakens.'),
            ('A New Constellation', 'A new constellation bloomed overhead; the real adventure had just begun.', 'Adventure begins now.'),
        ],
    },
    'realistic_35mm': {
        'name': 'Midnight Confession (35mm Cinema Example)',
        'brief': 'On a rainy night in a quiet city cafe, two old friends confront a secret kept for five years.',
        'title': 'Midnight Confession',
        'logline': 'A tense, photorealistic 35mm TV drama exchange between two old friends meeting in a rain-streaked midnight cafe.',
        'continuity_note': 'Same rainy corner booth, warm tungsten table lamp, 35mm ARRI Alexa cinematography, natural skin texture.',
        'scenes': [
            ('The Rainy Cafe', 'As rain tapped against the glass, only one corner lamp still glowed inside.', 'One lamp glows in the rain.'),
            ('The Old Envelope', 'I kept this envelope sealed for five years. Tonight I want the truth.', 'Five years sealed.'),
            ('Reverse Shot', 'I stayed silent that night because that letter would have changed both our lives.', 'The truth behind the silence.'),
            ('No Turning Back', 'She left the envelope in the center of the table and never looked back.', 'No turning back.'),
        ],
    },
    'documentary_4k': {
        'name': 'Harbor at Dawn (Documentary Camera Example)',
        'brief': 'At golden sunrise, coastal fishermen prepare their wooden boats and head out to sea.',
        'title': 'Harbor at Dawn',
        'logline': 'A calm, natural-light documentary portrait of coastal fishermen preparing for dawn departure.',
        'continuity_note': 'Natural golden sunrise light, true-to-life colors, crisp 50mm documentary lens.',
        'scenes': [
            ('Morning Mist', 'Before the town wakes, the first engines echo softly across the harbor.', 'First engines at dawn.'),
            ('Folding the Nets', 'Every morning begins the same way: steady hands checking nets and coiled ropes.', 'Steady hands at work.'),
            ('The Captain Speaks', 'The sea speaks differently every day—if you listen to the wind, you find your way.', 'Listen to the wind.'),
            ('Out to Open Water', 'And as the first boat leaves the pier, a new day truly begins.', 'A new day begins.'),
        ],
    },
}


def get_style_example(style_id: str, language: str = 'tr') -> dict | None:
    """Return a full 20s example project dict for ``style_id`` in ``'tr'`` or ``'en'``."""
    base = STYLE_EXAMPLES.get(style_id)
    if base is None:
        return None
    if language != 'en' or style_id not in STYLE_EXAMPLES_EN:
        return base
    en = STYLE_EXAMPLES_EN[style_id]
    scenes = []
    for scene, (title, narration, caption) in zip(base['script']['scenes'], en['scenes']):
        scenes.append({
            **scene,
            'title': title,
            'narration': narration,
            'caption': caption,
        })
    return {
        **base,
        'name': en['name'],
        'brief': en['brief'],
        'script': {
            **base['script'],
            'title': en['title'],
            'logline': en['logline'],
            'continuity_note': en['continuity_note'],
            'scenes': scenes,
        },
    }


def _resolve_style_artwork(root, style_id: str, temp_dir):
    """Return a raster PNG/JPG path for ``style_id`` (live ComfyUI sample > bundled raster > palette card)."""
    from pathlib import Path
    from PIL import Image, ImageDraw
    from . import media

    root = Path(root)
    live = root / 'style_samples' / f'{style_id}.png'
    if live.is_file() and live.stat().st_size > 1000:
        return live

    entry = next((item for item in media.STYLE_CATALOG if item['id'] == style_id), None)
    if entry:
        rel = entry['default_preview'].lstrip('/')
        for base in (root.parent / 'frontend' / 'dist', root.parent / 'frontend' / 'public'):
            candidate = base / rel
            if candidate.is_file() and candidate.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
                return candidate

    # Fallback clean gradient artwork using the style's own palette while ComfyUI sample renders
    fallback = Path(temp_dir) / f'{style_id}-fallback.png'
    palette = (entry or {}).get('palette') or ['#1c3238', '#d98845', '#f4d399']
    def _hex_rgb(code):
        code = code.lstrip('#')
        return tuple(int(code[i:i + 2], 16) for i in (0, 2, 4))
    c1 = _hex_rgb(palette[0])
    c2 = _hex_rgb(palette[min(1, len(palette) - 1)])
    c3 = _hex_rgb(palette[min(2, len(palette) - 1)])
    w, h = 540, 960
    img = Image.new('RGB', (w, h), c1)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    draw.ellipse([w // 2 - 150, h // 3 - 150, w // 2 + 150, h // 3 + 150], fill=c3)
    img.save(fallback)
    return fallback


def build_style_demo_video(root, style_id: str, language: str = 'tr', *, force: bool = False):
    """Render and cache a playable 20-second narrated/subtitled/BGM MP4 demo for a style."""
    import shutil
    import tempfile
    from pathlib import Path
    from . import media, providers
    from .models import catalog, voice_path

    lang = 'en' if language == 'en' else 'tr'
    example = get_style_example(style_id, lang)
    if example is None:
        raise ValueError(f'Stil örneği bulunamadı: {style_id}')

    root = Path(root)
    demos_dir = root / 'style_demos'
    demos_dir.mkdir(parents=True, exist_ok=True)
    scene_frames_dir = demos_dir / style_id
    target = demos_dir / f'{style_id}_{lang}.mp4'
    live_sample = root / 'style_samples' / f'{style_id}.png'
    scene_mtimes = [
        p.stat().st_mtime
        for pattern in ('scene-*.png', 'scene-*.mp4')
        for p in (scene_frames_dir.glob(pattern) if scene_frames_dir.is_dir() else [])
        if p.is_file()
    ]
    newest_input = max([live_sample.stat().st_mtime] if live_sample.is_file() else [0.0], default=0.0)
    if scene_mtimes:
        newest_input = max(newest_input, max(scene_mtimes))
    if (
        not force
        and target.is_file()
        and target.stat().st_size > 10_000
        and target.stat().st_mtime >= newest_input
    ):
        return target

    installed = catalog()
    voice_id = next(
        (m['id'] for m in installed if m['kind'] == 'voice' and m.get('ready') and m.get('language') == lang),
        next((m['id'] for m in installed if m['kind'] == 'voice' and m.get('ready')), 'tr_TR-dfki-medium'),
    )
    voice = media.load_voice(voice_path(voice_id))
    scenes = example['script']['scenes']

    with tempfile.TemporaryDirectory(prefix=f'demo-{style_id}-{lang}-') as tmp:
        work = Path(tmp)
        fallback_artwork = _resolve_style_artwork(root, style_id, work)
        out_w, out_h = 540, 960
        fps = 24
        # 4 distinct smooth Ken Burns camera moves so each 5s scene feels alive
        motions = [
            "zoompan=z='min(1.16,1+0.0012*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "zoompan=z='1.12':x='(iw-iw/zoom)*on/120':y='ih/2-(ih/zoom/2)'",
            "zoompan=z='1.12':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/120)'",
            "zoompan=z='max(1.0,1.16-0.0012*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        ]
        parts = []
        subtitles = []
        clock = 0.0
        cue_idx = 1
        for idx, sc in enumerate(scenes):
            dur = float(sc['duration'])
            scene_clip = scene_frames_dir / f'scene-{idx + 1:02d}.mp4'
            scene_art = scene_frames_dir / f'scene-{idx + 1:02d}.png'
            wav_path = work / f'scene-{idx + 1:02d}.wav'
            wav_dur = media.synthesize(voice, sc['narration'], wav_path)
            part_path = work / f'part-{idx + 1:02d}.mp4'
            fade_out = max(0.0, dur - 0.25)
            if scene_clip.is_file() and scene_clip.stat().st_size > 10_000:
                # Real AI-generated video clip (strip model audio and attach real Piper narration)
                vf = (
                    f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
                    f"crop={out_w}:{out_h},setsar=1,fps={fps},"
                    f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out:.2f}:d=0.25,format=yuv420p"
                )
                providers.run([
                    'ffmpeg', '-y', '-i', scene_clip, '-i', wav_path,
                    '-t', str(dur), '-map', '0:v:0', '-map', '1:a:0',
                    '-vf', vf, '-af', 'adelay=60,apad',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
                    '-c:a', 'aac', '-ar', '48000', part_path,
                ])
            else:
                frame_source = scene_art if (scene_art.is_file() and scene_art.stat().st_size > 1000) else fallback_artwork
                motion = motions[idx % len(motions)]
                vf = (
                    f"scale={out_w * 2}:{out_h * 2}:force_original_aspect_ratio=increase,"
                    f"crop={out_w * 2}:{out_h * 2},"
                    f"{motion}:d={int(round(dur * fps))}:s={out_w}x{out_h}:fps={fps},"
                    f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out:.2f}:d=0.25,format=yuv420p"
                )
                providers.run([
                    'ffmpeg', '-y', '-loop', '1', '-i', frame_source, '-i', wav_path,
                    '-t', str(dur), '-map', '0:v:0', '-map', '1:a:0',
                    '-vf', vf, '-af', 'adelay=60,apad',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
                    '-c:a', 'aac', '-ar', '48000', part_path,
                ])
            parts.append(f"file '{part_path.name}'")
            # 1-to-1 voice-synced subtitles matching exact spoken narration and spoken duration
            for c_start, c_end, c_text in media.timed_caption_cues(sc['narration'], clock + 0.06, min(dur - 0.08, wav_dur)):
                subtitles.append(f"{cue_idx}\n{media.srt_time(c_start)} --> {media.srt_time(c_end)}\n{c_text}")
                cue_idx += 1
            clock += dur

        (work / 'concat.txt').write_text('\n'.join(parts), encoding='utf-8')
        (work / 'captions.srt').write_text('\n\n'.join(subtitles), encoding='utf-8')
        joined = work / 'joined.mp4'
        sub_style = (
            "FontName=Segoe UI,Fontsize=13,Bold=1,"
            "PrimaryColour=&H00F4EFE6,OutlineColour=&H00121418,"
            "BorderStyle=1,Outline=1.2,Shadow=0.6,MarginV=34,MarginL=26,MarginR=26"
        )
        providers.run(
            [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat.txt',
                '-vf', f"subtitles=captions.srt:force_style='{sub_style}'",
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=7',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
                '-c:a', 'aac', '-movflags', '+faststart', joined,
            ],
            cwd=work,
        )
        bgm_preset = example.get('bgm_preset') or 'calm_ambient'
        bgm_path = media.ensure_bgm_file(bgm_preset, root / 'bgm')
        final_tmp = work / 'final.mp4'
        filter_complex = (
            "[0:a]asplit=2[voice][sc];"
            "[1:a]volume=0.16[bgm];"
            "[bgm][sc]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=350[ducked];"
            "[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2,alimiter=limit=0.95[outa]"
        )
        providers.run([
            'ffmpeg', '-y', '-i', joined, '-stream_loop', '-1', '-i', bgm_path,
            '-filter_complex', filter_complex,
            '-map', '0:v:0', '-map', '[outa]',
            '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-shortest', '-movflags', '+faststart',
            final_tmp,
        ])
        staging = target.with_suffix('.tmp.mp4')
        shutil.copyfile(final_tmp, staging)
        staging.replace(target)
    return target


def style_demo_status(root, style_id: str) -> str:
    """Return 'ai_video' if all 4 AI clips exist, 'scenes_still' if all 4 scene PNGs exist, else 'preview'."""
    from pathlib import Path
    scene_dir = Path(root) / 'style_demos' / style_id
    if not scene_dir.is_dir():
        return 'preview'
    clips = [p for p in scene_dir.glob('scene-*.mp4') if p.stat().st_size > 10_000]
    if len(clips) >= 4:
        return 'ai_video'
    pngs = [p for p in scene_dir.glob('scene-*.png') if not p.name.endswith('-last.png') and p.stat().st_size > 10_000]
    if len(pngs) >= 4:
        return 'scenes_still'
    return 'preview'


def render_style_demo_scenes(root, style_id: str, *, video_mode: str = 'still', on_progress=None, cancel_check=None):
    """Generate 4 distinct scene frames (and optionally FreeVideo AI clips) for a style, then rebuild TR & EN 20s demos."""
    from pathlib import Path
    from . import media, providers
    from .models import catalog
    from .schema import Settings

    example = get_style_example(style_id, 'tr')
    if example is None:
        raise ValueError(f'Stil örneği bulunamadı: {style_id}')
    style_prompt = media.STYLE_PRESETS[style_id]
    root = Path(root)
    scene_dir = root / 'style_demos' / style_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    installed = catalog()
    if video_mode == 'video':
        # High / Cinematic mode: Qwen Image 2.1 + FreeVideo
        best_image = 'qwen-image-21'
    else:
        # Fast (ltxv) or Balanced (balanced = FLUX.2 + FreeVideo) or Still
        best_image = next(
            (m['id'] for m in installed if m['kind'] == 'image' and m.get('ready')),
            'qwen-image-21',
        )
    base_settings = Settings(image=best_image).model_dump()
    scenes = example['script']['scenes']

    for idx, sc in enumerate(scenes, 1):
        out_png = scene_dir / f'scene-{idx:02d}.png'
        if not (out_png.is_file() and out_png.stat().st_size > 10_000):
            prompt = f"{style_prompt}. {sc['visual_prompt']} No text, no watermark."
            negative = sc.get('negative_prompt') or 'text, watermark, blurry, low quality'
            if on_progress:
                on_progress(f"{style_id} · Sahne {idx}/{len(scenes)} ilk kare ({sc['title']}) üretiliyor…")
            providers.generate_image(
                prompt,
                negative,
                out_png,
                {**base_settings, 'seed': 743 + idx * 17},
                on_progress=(lambda msg, i=idx: on_progress(f"{style_id} · Sahne {i}/{len(scenes)} · {msg}")) if on_progress else None,
                cancel_check=cancel_check,
            )

        if video_mode in ('video', 'balanced', 'ltxv'):
            out_clip = scene_dir / f'scene-{idx:02d}.mp4'
            if not (out_clip.is_file() and out_clip.stat().st_size > 10_000):
                last_png = None
                if sc.get('end_prompt'):
                    candidate_last = scene_dir / f'scene-{idx:02d}-last.png'
                    if not (candidate_last.is_file() and candidate_last.stat().st_size > 10_000):
                        if on_progress:
                            on_progress(f"{style_id} · Sahne {idx}/{len(scenes)} son kare üretiliyor…")
                        providers.generate_image(
                            f"{style_prompt}. Same scene, camera and characters. {sc['end_prompt']} No text, no watermark.",
                            sc.get('negative_prompt') or 'text, watermark, blurry, low quality',
                            candidate_last,
                            {**base_settings, 'seed': 743 + idx * 17},
                            [out_png],
                            on_progress=(lambda msg, i=idx: on_progress(f"{style_id} · Sahne {i}/{len(scenes)} son kare · {msg}")) if on_progress else None,
                            cancel_check=cancel_check,
                        )
                    last_png = candidate_last

                raw_clip = scene_dir / f'scene-{idx:02d}.raw.mp4'
                if video_mode == 'ltxv':
                    if on_progress:
                        on_progress(f"{style_id} · Sahne {idx}/{len(scenes)} LTX-Video hızlı AI klip üretiliyor…")
                    providers.ltxv_video(
                        sc.get('motion_prompt') or sc['visual_prompt'],
                        out_png,
                        last_png,
                        float(sc['duration']),
                        raw_clip,
                        {**base_settings, 'seed': 743 + idx * 17},
                        on_progress=(lambda msg, i=idx: on_progress(f"{style_id} · Sahne {i}/{len(scenes)} · {msg}")) if on_progress else None,
                        cancel_check=cancel_check,
                    )
                else:
                    if on_progress:
                        on_progress(f"{style_id} · Sahne {idx}/{len(scenes)} FreeVideo AI klip üretiliyor…")
                    providers.freevideo(
                        sc.get('motion_prompt') or sc['visual_prompt'],
                        out_png,
                        last_png,
                        [],
                        float(sc['duration']),
                        raw_clip,
                        {**base_settings, 'seed': 743 + idx * 17},
                        on_progress=(lambda msg, i=idx: on_progress(f"{style_id} · Sahne {i}/{len(scenes)} · {msg}")) if on_progress else None,
                        cancel_check=cancel_check,
                    )
                # Strip model-generated audio cleanly
                providers.run([
                    'ffmpeg', '-y', '-i', raw_clip,
                    '-map', '0:v:0', '-c:v', 'copy', '-an', '-movflags', '+faststart',
                    out_clip,
                ])
                raw_clip.unlink(missing_ok=True)

    if on_progress:
        on_progress(f'{style_id} · 20 sn TR ve EN örnek videolar birleştiriliyor…')
    tr_mp4 = build_style_demo_video(root, style_id, 'tr', force=True)
    en_mp4 = build_style_demo_video(root, style_id, 'en', force=True)
    return tr_mp4, en_mp4
