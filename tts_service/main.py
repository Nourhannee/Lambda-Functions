from flask import Flask, request, jsonify
import boto3, uuid, os
from kafka import KafkaProducer, KafkaConsumer
from gtts import gTTS
from pydub import AudioSegment

app = Flask(__name__)

# AWS S3
TTS_BUCKET = os.getenv('TTS_BUCKET', 'tts-service-storage-dev-bucket')
s3 = boto3.client('s3')

# Kafka Producer
KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092')
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/api/tts/synthesize', methods=['POST'])
def synthesize():
    data = request.json
    text = data['text']
    lang = data.get('lang', 'en')
    fmt = data.get('format', 'mp3')
    audio_id = str(uuid.uuid4())

    # Generate TTS audio
    audio_file = f'/tmp/{audio_id}.mp3'
    tts = gTTS(text=text, lang=lang)
    tts.save(audio_file)

    # Convert format if needed
    if fmt != 'mp3':
        sound = AudioSegment.from_file(audio_file)
        audio_file_fmt = f'/tmp/{audio_id}.{fmt}'
        sound.export(audio_file_fmt, format=fmt)
        os.remove(audio_file)
        audio_file = audio_file_fmt

    # Upload to S3
    s3.upload_file(audio_file, TTS_BUCKET, f'{audio_id}.{fmt}')

    # Cleanup temp file
    os.remove(audio_file)

    # Produce Kafka event
    producer.send('audio.generation.completed', {
        'audio_id': audio_id,
        'format': fmt,
        'bucket': TTS_BUCKET,
        'status': 'completed'
    })

    return jsonify({'audio_id': audio_id}), 201

@app.route('/api/tts/audio/<audio_id>', methods=['GET'])
def get_audio(audio_id):
    fmt = request.args.get('format', 'mp3')
    url = s3.generate_presigned_url(
        'get_object', 
        Params={'Bucket': TTS_BUCKET, 'Key': f'{audio_id}.{fmt}'},
        ExpiresIn=3600
    )
    return jsonify({'url': url})

@app.route('/api/tts/audio/<audio_id>', methods=['DELETE'])
def delete_audio(audio_id):
    fmt = request.args.get('format', 'mp3')
    s3.delete_object(Bucket=TTS_BUCKET, Key=f'{audio_id}.{fmt}')
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
