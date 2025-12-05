# Folklore Entry Template & Examples

This document provides templates and examples for creating folklore database entries.

---

## Entry Template

Copy this template when creating new entries:

```json
{
  "id": "XXX",
  "name": "Name in English",
  "name_russian": "Имя по-русски",
  "type": "house_spirit|water_spirit|forest_spirit|witch|hero|creature|ritual|superstition",
  "region": "Geographic region (e.g., All Russia, Northern Russia, Siberia)",
  "story_short": "2-3 sentence hook in English for international audiences.",
  "story_full": "Полный текст на русском языке для озвучивания. Длина 150-200 символов для 28-30 секунд. Включает начало, развитие и мораль.",
  "story_full_en": "English translation for reference and documentation purposes.",
  "moral": "One sentence key takeaway or lesson",
  "keywords": ["keyword1", "keyword2", "keyword3", "русское1", "русское2"],
  "visual_tags": ["unsplash_tag1", "unsplash_tag2", "unsplash_tag3"],
  "voice_tone": "warm_grandfather|mysterious_elder|energetic_youth|solemn_narrator",
  "duration_target": 28,
  "category": "household_spirit|water_spirit|forest_spirit|supernatural_being|hero|creature|ritual|superstition",
  "hashtags": "#russianfolklore #tag2 #tag3"
}
```

---

## Field Descriptions

### Required Fields

**id** (string)
- Format: 3 digits (001-075)
- Must be unique
- Sequential recommended but not required

**name** (string)
- English transliteration
- Title case
- Example: "Domovoi", "Baba Yaga"

**name_russian** (string)
- Original Russian name in Cyrillic
- Example: "Домовой", "Баба Яга"

**type** (string)
- Valid values:
  - `house_spirit` - Домовой, Кикимора, etc.
  - `water_spirit` - Русалка, Водяной, etc.
  - `forest_spirit` - Леший, etc.
  - `field_spirit` - Полевой, Полудница
  - `witch` - Баба Яга, Ведьма
  - `hero` - Илья Муромец, Добрыня
  - `creature` - Жар-птица, Змей Горыныч
  - `ritual` - Иван Купала, Масленица
  - `superstition` - Salt spilling, mirror breaking

**story_full** (string)
- Russian narration text (what TTS will read)
- Target length: 150-200 characters
- Target duration: 28-30 seconds
- Include: beginning, development, moral
- Use natural Russian speech patterns
- Avoid complex words for TTS

**visual_tags** (array of strings)
- Search terms for Unsplash API
- 4-6 tags recommended
- Use English terms
- Be descriptive but not too specific
- Examples: "mystical", "old wooden house", "fireplace", "warm light"

**voice_tone** (string)
- Valid values:
  - `warm_grandfather` - Friendly, storytelling (Dmitry)
  - `mysterious_elder` - Slow, enigmatic (Svetlana)
  - `energetic_youth` - Upbeat, modern (Dariya)
  - `solemn_narrator` - Formal, serious (Dmitry)

### Recommended Fields

**story_short** (string)
- English hook/summary
- 2-3 sentences
- For international audience

**story_full_en** (string)
- English translation of story_full
- For reference and documentation

**moral** (string)
- Key takeaway in one sentence
- Will be displayed on collage

**keywords** (array)
- SEO keywords
- Mix English and Russian
- Used for hashtags and search

**hashtags** (string)
- Pre-generated Instagram hashtags
- Space-separated
- Start with #
- Mix popular and niche

**category** (string)
- For analytics and variety
- Groups similar folklore types

**duration_target** (number)
- Target duration in seconds
- Typically 25-31 for 30s videos
- TTS speed will auto-adjust

---

## Complete Examples

### Example 1: House Spirit (Simple)

```json
{
  "id": "001",
  "name": "Domovoi",
  "name_russian": "Домовой",
  "type": "house_spirit",
  "region": "All Russia",
  "story_short": "The house spirit who lives behind the stove and protects families who respect him.",
  "story_full": "В каждом русском доме живёт домовой — хранитель очага и семейного благополучия. Он живёт за печкой, следит за порядком и помогает хозяевам. Но если его разозлить, может напустить беды. Чтобы задобрить домового, оставляйте ему молоко и хлеб на ночь.",
  "story_full_en": "In every Russian home lives a domovoi - guardian of the hearth and family wellbeing. He lives behind the stove, watches over order, and helps the household. But if angered, he can bring troubles. To appease the domovoi, leave him milk and bread at night.",
  "moral": "Respect your home and it will protect you",
  "keywords": ["spirit", "house", "fireplace", "guardian", "protection", "домовой", "дух"],
  "visual_tags": ["cozy interior", "fireplace", "old wooden house", "mystical", "warm light", "russian home"],
  "voice_tone": "warm_grandfather",
  "duration_target": 28,
  "category": "household_spirit",
  "hashtags": "#russianfolklore #domovoi #домовой #slavicmythology #folklore #mythology #russianculture"
}
```

### Example 2: Supernatural Being (Complex)

```json
{
  "id": "002",
  "name": "Baba Yaga",
  "name_russian": "Баба Яга",
  "type": "witch",
  "region": "All Russia",
  "story_short": "The fearsome witch who lives in a hut on chicken legs deep in the forest.",
  "story_full": "Глубоко в дремучем лесу стоит избушка на курьих ножках. В ней живёт Баба Яга — древняя ведьма с костяной ногой. Она летает в ступе, заметая следы метлой. К Бабе Яге приходят герои за советом или волшебным предметом. Но будь осторожен: она может как помочь, так и съесть незваного гостя.",
  "story_full_en": "Deep in the dense forest stands a hut on chicken legs. There lives Baba Yaga - an ancient witch with a bone leg. She flies in a mortar, sweeping her tracks with a broom. Heroes come to Baba Yaga for advice or magical items. But beware: she may either help or eat an uninvited guest.",
  "moral": "Wisdom has its price, approach with respect",
  "keywords": ["witch", "forest", "magic", "hut", "chicken legs", "баба яга", "ведьма", "избушка"],
  "visual_tags": ["dark forest", "old hut", "mystical", "witch", "magic", "slavic", "eerie", "moss"],
  "voice_tone": "mysterious_elder",
  "duration_target": 30,
  "category": "supernatural_being",
  "hashtags": "#babayaga #бабаяга #russianfolklore #witchcraft #slavicmythology #folklore #darkfantasy"
}
```

### Example 3: Water Spirit (Narrative)

```json
{
  "id": "003",
  "name": "Rusalka",
  "name_russian": "Русалка",
  "type": "water_spirit",
  "region": "Southern Russia, Ukraine",
  "story_short": "Beautiful water maidens who lure men into rivers with their enchanting songs.",
  "story_full": "На берегах рек и озёр живут русалки — прекрасные девы с длинными зелёными волосами. По ночам они расчёсывают косы и поют заворожи́вающие песни. Мужчины, услышавшие их голоса, идут к воде и тонут. Русалки — это души девушек, утонувших до свадьбы.",
  "story_full_en": "On the banks of rivers and lakes live rusalki - beautiful maidens with long green hair. At night they comb their tresses and sing enchanting songs. Men who hear their voices walk into the water and drown. Rusalki are the souls of girls who drowned before their wedding.",
  "moral": "Beauty can be dangerous, stay vigilant",
  "keywords": ["water", "spirit", "river", "mermaid", "maiden", "русалка", "вода", "река"],
  "visual_tags": ["river", "water", "mysterious woman", "long hair", "moonlight", "slavic", "ethereal", "mist"],
  "voice_tone": "mysterious_elder",
  "duration_target": 29,
  "category": "water_spirit",
  "hashtags": "#rusalka #русалка #waterespirit #mermaid #slavicmythology #folklore #siren"
}
```

---

## Tips for Writing Entries

### Story Writing (story_full)

**Length Guidelines:**
- Target: 150-200 characters in Russian
- This produces ~25-30 seconds of speech
- Use `python scripts/generate_voice.py` to test

**Structure:**
1. **Introduction** (1-2 sentences): Who/what is this?
2. **Description** (2-3 sentences): Key characteristics, behaviors
3. **Moral/Warning** (1 sentence): Takeaway message

**Language Tips:**
- Use simple, clear Russian
- Avoid overly complex words (TTS struggles with them)
- Include stress marks (́) if TTS mispronounces
- Use natural speech patterns
- Tell a story, don't just list facts

### Visual Tags Selection

**Good tags:**
- Descriptive: "old wooden house", "mystical forest"
- Atmospheric: "warm light", "moonlight", "fog"
- Specific: "fireplace", "river", "wheat field"
- Emotional: "mysterious", "cozy", "eerie"

**Bad tags:**
- Too specific: "domovoi", "baba yaga" (won't find images)
- Too generic: "photo", "image"
- Non-visual: "folklore", "story"

**Strategy:**
- Use 4-6 tags
- Mix broad + specific
- Consider time of day, lighting, mood
- Check Unsplash to see if images exist

### Voice Tone Selection

**warm_grandfather** → Best for:
- Household spirits (Domovoi)
- Friendly creatures
- Teaching/wisdom stories
- Positive folklore

**mysterious_elder** → Best for:
- Water spirits (Rusalka)
- Dark forests
- Warnings and curses
- Enigmatic beings

**energetic_youth** → Best for:
- Heroes' adventures
- Celebratory rituals
- Modern interpretations
- Joyful stories

**solemn_narrator** → Best for:
- Epic heroes
- Tragic stories
- Historical context
- Serious lessons

---

## Validation Checklist

Before adding an entry, verify:

- [ ] ID is unique (001-075)
- [ ] All required fields present
- [ ] story_full is 150-200 characters
- [ ] story_full is natural Russian (no awkward phrases)
- [ ] visual_tags will return good Unsplash results
- [ ] voice_tone matches the story mood
- [ ] hashtags are relevant and properly formatted
- [ ] No typos in Russian text
- [ ] Moral is clear and concise

---

## Testing New Entries

Test before adding to main database:

```bash
# 1. Test TTS generation
python scripts/generate_voice.py "Your story_full text here"
# Check: Does it sound natural? Is duration ~28-30s?

# 2. Test image fetching
python scripts/fetch_images.py "visual_tag1 visual_tag2"
# Check: Are images relevant and high quality?

# 3. Test full generation
# Add entry to folklore_database.json, then:
python scripts/generate_daily_content.py
```

---

## Content Ideas (72 more needed)

### Household Spirits (15 more)
- Kikimora (Кикимора) - chaos spirit
- Ovinnik (Овинник) - barn spirit
- Bannik (Банник) - bathhouse spirit
- Dvorovoi (Дворовой) - yard spirit

### Water Spirits (8 more)
- Vodyanoy (Водяной) - water demon
- Bolotnik (Болотник) - swamp spirit

### Forest Spirits (8 more)
- Leshy (Леший) - forest guardian
- Poludnitsa (Полудница) - noonday demon

### Heroes (12 more)
- Ilya Muromets (Илья Муромец)
- Dobrynya Nikitich (Добрыня Никитич)
- Alyosha Popovich (Алёша Попович)

### Creatures (12 more)
- Firebird (Жар-птица)
- Zmey Gorynych (Змей Горыныч)
- Koschei the Deathless (Кощей Бессмертный)

### Rituals & Holidays (10 more)
- Ivan Kupala (Иван Купала)
- Maslenitsa (Масленица)
- Kolyada (Коляда)

### Superstitions (7 more)
- Breaking mirrors
- Salt spilling
- Black cats
- Sitting at corner of table
- Whistling indoors

---

## Resources

### Research Sources
- Russian folklore encyclopedias
- Ethnographic museums
- Academic papers on Slavic mythology
- Classic Russian fairy tales

### Unsplash Collections
- Russian Culture: https://unsplash.com/s/photos/russian-culture
- Mystical: https://unsplash.com/s/photos/mystical
- Slavic: https://unsplash.com/s/photos/slavic

### TTS Testing
```bash
# Test different voices
edge-tts --list-voices | grep "ru-RU"

# Generate test audio
edge-tts --voice ru-RU-DmitryNeural --text "Тест" --write-media test.mp3
```

---

**Happy folklore documenting!** 🪆
